import sys
import requests

TOKEN = "8673260750:AAGAGPx0eHEjdOkz9VH0nOnWTSeXcKzeRpE"
CHAT_ID = "947236244"

def send_message(message, parse_mode="Markdown", reply_markup=None):
    if CHAT_ID == "YOUR_CHAT_ID":
        print("Error: CHAT_ID not set. Please message the bot first.")
        return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID, 
        "text": message, 
        "parse_mode": parse_mode
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    requests.post(url, json=payload)

def send_approval_request(task_name, summary, file_path=None):
    """
    Sends a structured approval request with Inline Buttons.
    """
    msg = (f"🟡 *APPROVAL REQUIRED: {task_name}*\n\n"
           f"📝 *Summary:*\n{summary}\n\n")
    if file_path:
        msg += f"📂 *File:* `{file_path}`\n\n"
    
    markup = {
        "inline_keyboard": [[
            {"text": "✅ Approve", "callback_data": "approve"},
            {"text": "❌ Reject", "callback_data": "reject"}
        ]]
    }
    send_message(msg, reply_markup=markup)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Simple usage: python3 notify.py "message"
        send_message(sys.argv[1])
    else:
        print("Usage: python3 notify.py 'Your message here'")
