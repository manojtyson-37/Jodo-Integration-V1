from flask import Blueprint, request, jsonify, render_template, send_from_directory
from datetime import datetime
import os
import uuid
import time
from ..utils.db import get_order_db, save_order_db
from ..utils.notifier import send_message
from ..webhooks.routes import deliver_webhook_async

sim_bp = Blueprint('simulation', __name__)

ORDER_DATA_FILE = 'orders.json'

@sim_bp.route('/<order_id>')
def checkout(order_id):
    """
    Renders the mock checkout page for a specific order.
    """
    order = get_order_db(order_id)
    
    if not order:
        return "Order not found", 404
        
    return render_template('checkout.html', 
                            order_id=order_id, 
                            amount=order['amount'], 
                            pg=order['pg'], 
                            customer=order['customer'],
                            callback_url=order.get('callback_url'))

@sim_bp.route('/<order_id>/pay', methods=['POST'])
def process_payment(order_id):
    """
    Simulates the payment processing, status updates, and webhooks.
    """
    data = request.get_json()
    success = data.get('success', False)
    # Removed blocking sleep to prevent worker congestion in cloud environments.
    # if latency > 0:
    #     time.sleep(min(latency, 10))
        
    order = get_order_db(order_id)
    
    if not order:
        return jsonify({"status": "error", "message": "Order not found"}), 404
        
    if order['status'] != 'created':
        return jsonify({"status": "error", "message": "Order already processed"}), 400
        
    # Update Status
    order['status'] = 'paid' if success else 'failed'
    order['updated_at'] = datetime.now().isoformat()
    if success:
        order['payment_id'] = f"pay_{uuid.uuid4().hex[:12]}"
        
    save_order_db(order_id, order)
    
    # Notify Admin
    msg = (f"💳 *Simulation: Payment {order['status'].upper()}*\n\n"
           f"Order ID: `{order_id}`\n"
           f"Amount: ₹{order['amount']}\n"
           f"User: {order['user_email']}")
    send_message(msg)
    
    # Trigger Webhooks if success
    if success:
        payload = {
            "event": "order.payment.debited",
            "data": {
                "id": order.get('payment_id', 'N/A'),
                "order_id": order_id,
                "amount": order['amount'],
                "currency": order['currency'],
                "status": "paid",
                "method": "simulator",
                "description": "Sandbox Payment Simulation"
            },
            "timestamp": datetime.now().isoformat()
        }
        deliver_webhook_async(order['user_email'], 'order.payment.debited', payload)
        
        # Simulate Settlement after another delay (30 seconds for test)
        # In a real system, this would be a separate background job
        def late_settle():
            time.sleep(30)
            order_late = get_order_db(order_id)
            if order_late and order_late['status'] == 'paid':
                order_late['status'] = 'settled'
                order_late['updated_at'] = datetime.now().isoformat()
                save_order_db(order_id, order_late)
                
                # Settle Webhook
                settle_payload = {
                    "event": "order.payment.settled",
                    "data": {
                        "id": f"setl_{uuid.uuid4().hex[:12]}",
                        "payment_id": order_late['payment_id'],
                        "order_id": order_id,
                        "amount": order_late['amount'],
                        "fee": order_late['amount'] * 0.02, # 2% simulated fee
                        "tax": (order_late['amount'] * 0.02) * 0.18, # 18% GST on fee
                    },
                    "timestamp": datetime.now().isoformat()
                }
                deliver_webhook_async(order_late['user_email'], 'order.payment.settled', settle_payload)

        import threading
        threading.Thread(target=late_settle).start()
        
    return jsonify({
        "status": "success",
        "order_status": order['status']
    })
