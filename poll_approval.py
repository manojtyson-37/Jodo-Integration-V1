import time
import requests
from notify import TOKEN, CHAT_ID

def check_for_approval(timeout=60, poll_interval=5):
    """
    Polls Telegram for an 'Approve' or 'OK' message.
    Returns True if approved, False otherwise.
    """
    start_time = time.time()
    last_update_id = 0
    
    # Get initial update ID to ignore old messages
    res = requests.get(f"https://api.telegram.org/bot{TOKEN}/getUpdates").json()
    if res["ok"] and res["result"]:
        last_update_id = res["result"][-1]["update_id"]

    print(f"Waiting for approval (timeout: {timeout}s)...")
    
    while time.time() - start_time < timeout:
        url = f"https://api.telegram.org/bot{TOKEN}/getUpdates?offset={last_update_id + 1}"
        try:
            res = requests.get(url).json()
            if res["ok"] and res["result"]:
                for update in res["result"]:
                    last_update_id = update["update_id"]
                    message = update.get("message", {})
                    text = message.get("text", "").strip().lower()
                    sender_id = str(message.get("from", {}).get("id", ""))
                    
                    if sender_id == CHAT_ID and text in ["approve", "ok", "yes"]:
                        print("✅ Approval received via Telegram!")
                        return True
        except Exception as e:
            print(f"Polling error: {e}")
            
        time.sleep(poll_interval)
    
    print("⏰ Approval timeout.")
    return False

if __name__ == "__main__":
    # Test polling
    if check_for_approval(timeout=30):
        print("Approved!")
    else:
        print("Not approved.")
