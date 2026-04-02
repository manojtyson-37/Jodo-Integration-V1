import json
import os
import time
import uuid
import threading
import requests
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from ..utils.storage import load_json, save_json

webhooks_bp = Blueprint('webhooks', __name__)

WEBHOOK_DATA_FILE = 'webhooks.json'
WEBHOOK_LOG_FILE = 'webhook_logs.json'
USER_DATA_FILE = 'users.json'

def get_user_email():
    """
    Robustly get the user email from JSON payload or query parameters.
    Uses silent=True to avoid 415 errors on GET requests.
    """
    email = request.args.get('email')
    if not email:
        data = request.get_json(silent=True) or {}
        email = data.get('email')
    return email

@webhooks_bp.route('', methods=['GET'])
def list_webhooks():
    email = get_user_email()
    if not email:
        return jsonify({"status": "error", "message": "Email required"}), 400
    
    webhooks = load_json(WEBHOOK_DATA_FILE)
    user_hooks = webhooks.get(email, [])
    
    # Automatic Migration: Convert strings to objects if found
    migrated = False
    for i, hook in enumerate(user_hooks):
        if isinstance(hook, str):
            user_hooks[i] = {"url": hook, "events": ["*"]} # "*" means all events
            migrated = True
    
    if migrated:
        webhooks[email] = user_hooks
        save_json(WEBHOOK_DATA_FILE, webhooks)
    
    return jsonify({
        "status": "success",
        "data": user_hooks
    })

@webhooks_bp.route('', methods=['POST'])
def add_webhook():
    data = request.get_json()
    email = data.get('email')
    url = data.get('url')
    events = data.get('events', ['*']) # Default to all events
    
    if not email or not url:
        return jsonify({"status": "error", "message": "Email and URL required"}), 400
        
    webhooks = load_json(WEBHOOK_DATA_FILE)
    if email not in webhooks:
        webhooks[email] = []
        
    # Check for duplicates by URL
    existing_urls = [h['url'] if isinstance(h, dict) else h for h in webhooks[email]]
    if url in existing_urls:
        return jsonify({"status": "error", "message": "Webhook URL already exists"}), 400
        
    webhooks[email].append({
        "url": url,
        "events": events if isinstance(events, list) else ['*']
    })
    save_json(WEBHOOK_DATA_FILE, webhooks)
    
    return jsonify({
        "status": "success",
        "message": "Webhook registered!"
    })

@webhooks_bp.route('/<int:index>', methods=['DELETE'])
def delete_webhook(index):
    email = request.args.get('email')
    if not email:
        return jsonify({"status": "error", "message": "Email required"}), 400
        
    webhooks = load_json(WEBHOOK_DATA_FILE)
    user_hooks = webhooks.get(email, [])
    
    if index < 0 or index >= len(user_hooks):
        return jsonify({"status": "error", "message": "Invalid index"}), 400
        
    user_hooks.pop(index)
    webhooks[email] = user_hooks
    save_json(WEBHOOK_DATA_FILE, webhooks)
    
    return jsonify({"status": "success", "message": "Webhook removed"})

@webhooks_bp.route('/logs', methods=['GET'])
def list_logs():
    email = get_user_email()
    if not email:
        return jsonify({"status": "error", "message": "Email required"}), 400
        
    logs = load_json(WEBHOOK_LOG_FILE, default=[])
    user_logs = [l for l in logs if l.get('user_email') == email]
    user_logs.reverse() # Show most recent first
    
    return jsonify({
        "status": "success",
        "data": user_logs[:50]
    })

# --- Webhook Delivery Logic ---

def deliver_webhook_async(user_email, event_type, payload):
    thread = threading.Thread(target=delivery_worker, args=(user_email, event_type, payload))
    thread.start()

def delivery_worker(user_email, event_type, payload):
    """
    Background worker with absolute path resolution and stdout logging for terminal visibility.
    """
    # 1. Resolve absolute path to the data directory
    ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
    data_dir = os.path.join(ROOT_DIR, 'data')
    
    print(f"📦 INFO: Webhook Delivery Started | User: {user_email} | Event: {event_type}")

    webhooks_content = {}
    try:
        data_path = os.path.join(data_dir, WEBHOOK_DATA_FILE)
        with open(data_path, 'r') as f:
            webhooks_content = json.load(f)
    except Exception as e:
        print(f"❌ ERROR: Failed to load webhooks.json in background worker: {e}")
        return

    hooks = webhooks_content.get(user_email, [])
    if not hooks:
        print(f"⚠️ INFO: No webhooks found for user {user_email}")
        return

    for hook in hooks:
        try:
            # Standardize hook (handle migration on-the-fly in the worker as well)
            url = hook['url'] if isinstance(hook, dict) else hook
            events = hook.get('events', ['*']) if isinstance(hook, dict) else ['*']

            # Event Filtering
            if '*' not in events and event_type not in events:
                print(f"⏭️ INFO: Skipping {event_type} for {url} (Events configured: {events})")
                continue

            print(f"🚀 INFO: Attempting POST to {url} for event {event_type}")

            attempts = 0
            max_retries = 3
            backoff = 2
            success = False
            last_response = 0

            while attempts < max_retries:
                attempts += 1
                try:
                    response = requests.post(url, json=payload, timeout=10)
                    last_response = response.status_code
                    if response.status_code < 300:
                        success = True
                        print(f"✅ SUCCESS: Webhook delivered to {url} (Status: {last_response})")
                        break
                except Exception as e:
                    print(f"⚠️ TRY {attempts}/{max_retries} FAILED: {url} | Error: {e}")
                    last_response = 500

                if attempts < max_retries:
                    time.sleep(backoff ** attempts)

            # Log to webhook_logs.json
            log_entry = {
                "id": str(uuid.uuid4())[:8],
                "user_email": user_email,
                "event": event_type,
                "url": url,
                "status": "success" if success else "failed",
                "attempts": attempts,
                "response_code": last_response,
                "timestamp": datetime.now().isoformat(),
                "payload": payload
            }
            
            log_path = os.path.join(data_dir, WEBHOOK_LOG_FILE)
            logs = []
            if os.path.exists(log_path):
                with open(log_path, 'r') as f:
                    logs = json.load(f)
            logs.append(log_entry)
            with open(log_path, 'w') as f:
                json.dump(logs, f, indent=4)
        
        except Exception as e:
            print(f"💣 CRITICAL ERROR in delivery loop: {e}")
