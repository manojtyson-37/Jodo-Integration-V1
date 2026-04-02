import json
import os
import time
import uuid
import threading
import requests
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from ..utils.db import (
    save_webhook_db, 
    list_webhooks_db, 
    delete_webhook_db, 
    list_webhook_logs_db, 
    save_webhook_log_db
)

webhooks_bp = Blueprint('webhooks', __name__)

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
    
    user_hooks = list_webhooks_db(email)
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
        
    save_webhook_db(email, url, events)
    
    return jsonify({
        "status": "success",
        "message": "Webhook registered!"
    })

@webhooks_bp.route('/<int:index>', methods=['DELETE'])
def delete_webhook(index):
    # Note: DB-backed deletion uses URL since index is risky in a relational world
    email = request.args.get('email')
    url = request.args.get('url')
    if not email or not url:
        return jsonify({"status": "error", "message": "Email and URL required for deletion"}), 400
        
    delete_webhook_db(email, url)
    return jsonify({"status": "success", "message": "Webhook removed"})

@webhooks_bp.route('/logs', methods=['GET'])
def list_logs():
    email = get_user_email()
    if not email:
        return jsonify({"status": "error", "message": "Email required"}), 400
        
    user_logs = list_webhook_logs_db(email)
    return jsonify({
        "status": "success",
        "data": user_logs
    })

# --- Webhook Delivery Logic ---

def deliver_webhook_async(user_email, event_type, payload):
    thread = threading.Thread(target=delivery_worker, args=(user_email, event_type, payload))
    thread.start()

def delivery_worker(user_email, event_type, payload):
    """
    Background worker with DB-backed logging and stdout status.
    """
    print(f"📦 INFO: Webhook Delivery Started | User: {user_email} | Event: {event_type}")

    hooks = list_webhooks_db(user_email)
    if not hooks:
        print(f"⚠️ INFO: No webhooks found for user {user_email}")
        return

    for hook in hooks:
        try:
            url = hook['url']
            events = hook.get('events', ['*'])

            # Event Filtering
            if '*' not in events and event_type not in events:
                continue

            attempts = 0
            max_retries = 3
            success = False
            last_response = 0

            while attempts < max_retries:
                attempts += 1
                try:
                    response = requests.post(url, json=payload, timeout=10)
                    last_response = response.status_code
                    if response.status_code < 300:
                        success = True
                        break
                except Exception:
                    last_response = 500

                if attempts < max_retries:
                    time.sleep(2 ** attempts)

            # Log to DB
            log_entry = {
                "user_email": user_email,
                "event": event_type,
                "url": url,
                "status": "success" if success else "failed",
                "attempts": attempts,
                "response_code": last_response,
                "payload": payload
            }
            save_webhook_log_db(log_entry)
            print(f"{'✅' if success else '❌'} Webhook: {url} | Status: {last_response}")
        
        except Exception as e:
            print(f"💣 CRITICAL ERROR in delivery worker: {e}")
