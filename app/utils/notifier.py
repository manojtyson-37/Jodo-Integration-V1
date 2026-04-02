import requests

# Hardcoded for now as per current notify.py, but could be env vars later
TOKEN = "8673260750:AAGAGPx0eHEjdOkz9VH0nOnWTSeXcKzeRpE"
CHAT_ID = "947236244"

def send_message(message, parse_mode="Markdown", reply_markup=None):
    if not TOKEN or not CHAT_ID:
        return
        
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID, 
        "text": message, 
        "parse_mode": parse_mode
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"Telegram Notification Error: {e}")

def notify_new_user(email, name):
    msg = f"🆕 *New Developer Signed Up!*\n\nEmail: {email}\nName: {name}"
    send_message(msg)

def notify_login(email):
    msg = f"🔑 *Developer Logged In:*\n{email}"
    send_message(msg)

def notify_order_created(order_id, amount, customer_name):
    msg = (f"📦 *Order Created Successfully!*\n\n"
           f"Account: {customer_name}\n"
           f"Amount: ₹{amount}\n"
           f"Order ID: `{order_id}`")
    send_message(msg)
