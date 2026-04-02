from flask import Blueprint, request, jsonify
from datetime import datetime
import os
import uuid
from ..utils.storage import load_json, save_json
from ..utils.notifier import notify_order_created

orders_bp = Blueprint('orders', __name__)

ORDER_DATA_FILE = 'orders.json'
USER_DATA_FILE = 'users.json'

def get_auth_user():
    auth = request.authorization
    pg_header = request.headers.get('X-PG', 'jodo')
    
    if auth and auth.username:
        # Standard keys from server.py (simulation mode)
        if pg_header == 'razorpay' and auth.username == 'rzp_test_K0W8zUvD1S8R6C':
            return {'email': 'rzp_simulator', 'name': 'Razorpay Simulator'}
        elif pg_header == 'easebuzz' and request.headers.get('X-Merchant-Key') == '2P7S8793ST':
            return {'email': 'ebz_simulator', 'name': 'Easebuzz Simulator'}
        
        # Master Demo Credentials (Persistent across redeploys)
        if auth.username == 'jodo_sb_MASTER_KEY':
            return {'email': 'master@jodo.io', 'name': 'Master Demo'}
            
        # Local users
        users = load_json(USER_DATA_FILE)
        for email, user in users.items():
            if user['sandbox_key'] == auth.username:
                return {'email': email, 'name': user['name']}
    
    return None

@orders_bp.route('', methods=['POST'])
def create_order():
    user = get_auth_user()
    if not user:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
    
    data = request.get_json()
    pg_header = request.headers.get('X-PG', 'jodo')
    
    # Generate realistic Order ID based on PG
    if pg_header == 'razorpay':
        order_id = f"order_rzp_{os.urandom(4).hex()}"
    elif pg_header == 'easebuzz':
        order_id = f"EBZ_{os.urandom(4).hex().upper()}"
    else:
        order_id = f"order_{os.urandom(6).hex()}"

    # Payment URL points to our simulation checkout
    payment_url = f"/pay/{order_id}"

    # Handle Jodo-specific details array if present
    details = data.get("details", [])
    total_amount = data.get("amount")
    
    if details and total_amount is None:
        try:
            total_amount = sum(float(item.get("amount", 0)) for item in details)
        except (ValueError, TypeError):
            total_amount = 0
    
    # Standardize amount
    total_amount = total_amount or 0

    # Persist the order
    orders = load_json(ORDER_DATA_FILE)
    orders[order_id] = {
        "user_email": user['email'],
        "amount": total_amount,
        "currency": data.get("currency", "INR"),
        "details": details,  # Preserve official Jodo details
        "status": "created",
        "pg": pg_header,
        "customer": {
            "name": data.get("name"),
            "email": data.get("email"),
            "phone": data.get("phone")
        },
        "callback_url": data.get("callback_url"),
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "redirect_url": payment_url
    }
    save_json(ORDER_DATA_FILE, orders)
    
    notify_order_created(order_id, total_amount, data.get("name", "Customer"))
    
    return jsonify({
        "status": "success",
        "message": f"Order created in {pg_header.capitalize()} Sandbox",
        "data": {
            "id": order_id,
            "payment_url": payment_url,
            "request_id": f"Root=1-{uuid.uuid4().hex[:8]}",
            "timestamp": datetime.now().isoformat()
        }
    })

@orders_bp.route('/<order_id>', methods=['GET'])
def get_order(order_id):
    user = get_auth_user()
    if not user:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
        
    orders = load_json(ORDER_DATA_FILE)
    order = orders.get(order_id)
    
    if not order:
        return jsonify({"status": "error", "message": "Order not found"}), 404
        
    # Ensure user only sees their own orders (except simulators)
    if user['email'] not in ['rzp_simulator', 'ebz_simulator'] and order['user_email'] != user['email']:
        return jsonify({"status": "error", "message": "Unauthorized"}), 403
        
    return jsonify({
        "status": "success",
        "data": {
            "id": order_id,
            "status": order["status"],
            "amount": order["amount"],
            "currency": order["currency"],
            "pg": order["pg"],
            "created_at": order["created_at"],
            "updated_at": order["updated_at"]
        }
    })

@orders_bp.route('/list', methods=['GET'])
def list_orders():
    # Helper for Dashboard
    user_email = request.args.get('email')
    if not user_email:
        return jsonify({"status": "error", "message": "Email required"}), 400
        
    orders = load_json(ORDER_DATA_FILE)
    user_orders = [
        {"id": oid, **odata} 
        for oid, odata in orders.items() 
        if odata['user_email'] == user_email
    ]
    
    # Sort by recent
    user_orders.sort(key=lambda x: x['created_at'], reverse=True)
    
    return jsonify({
        "status": "success",
        "data": user_orders
    })

@orders_bp.route('/stats', methods=['GET'])
def get_user_stats():
    email = request.args.get('email')
    if not email:
        return jsonify({"status": "error", "message": "Email required"}), 400
        
    orders = load_json(ORDER_DATA_FILE)
    user_orders = [odata for odata in orders.values() if odata['user_email'] == email]
    
    # Calculate stats
    now = datetime.now()
    last_24h = [
        o for o in user_orders 
        if (now - datetime.fromisoformat(o['created_at'])).total_seconds() < 86400
    ]
    
    total_24h = len(last_24h)
    success_orders = [o for o in last_24h if o['status'] in ['paid', 'settled']]
    
    success_rate = (len(success_orders) / total_24h * 100) if total_24h > 0 else 100.0
    
    # Simulate realistic latency based on volume (aesthetic realism)
    import random
    avg_latency = random.randint(85, 140) if total_24h > 0 else 0

    return jsonify({
        "status": "success",
        "data": {
            "total_requests_24h": total_24h,
            "success_rate": round(success_rate, 1),
            "avg_latency_ms": avg_latency
        }
    })
