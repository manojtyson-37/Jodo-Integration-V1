import time
import requests
import json
from notify import TOKEN, CHAT_ID

def get_telegram_command(timeout=180, poll_interval=10):
    """
    Polls Telegram for any text message from the user.
    Returns the message text if found, or None if timed out.
    """
    start_time = time.time()
    last_update_id = 0
    
    # Get initial update ID to ignore old messages
    try:
        res = requests.get(f"https://api.telegram.org/bot{TOKEN}/getUpdates").json()
        if res["ok"] and res["result"]:
            last_update_id = res["result"][-1]["update_id"]
    except Exception as e:
        print(f"Error initializing listener: {e}")

    print(f"📡 *Listening for commands on Telegram (timeout: {timeout}s)...*")
    
    while time.time() - start_time < timeout:
        url = f"https://api.telegram.org/bot{TOKEN}/getUpdates?offset={last_update_id + 1}"
        try:
            res = requests.get(url).json()
            if res["ok"] and res["result"]:
                # Get the most recent message
                update = res["result"][-1]
                last_update_id = update["update_id"]
                message = update.get("message", {})
                text = message.get("text", "").strip()
                sender_id = str(message.get("from", {}).get("id", ""))
                
                if sender_id == CHAT_ID and text:
                    print(f"\n📥 *New Command from Telegram:* \"{text}\"")
                    return text
        except Exception as e:
            print(f"Polling error: {e}")
            
        time.sleep(poll_interval)
    
    print("\n⏰ *No new command received from Telegram.*")
    return None

if __name__ == "__main__":
    # Standard 3-minute listener
    command = get_telegram_command()
    if command:
        # We output in a format that the Agent can easily parse
        print(f"---COMMAND_START---\n{command}\n---COMMAND_END---")
