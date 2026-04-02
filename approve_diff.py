import sys
import argparse
import time
from notify import send_message, CHAT_ID, TOKEN
from poll_approval import check_for_approval

def send_diff_request(file_path, summary, diff_text=None):
    """
    Sends a detailed file change request with Inline Buttons.
    """
    msg = (f"🔍 *FILE APPROVAL REQUEST*\n\n"
           f"📂 *File:* `{file_path}`\n"
           f"📝 *Summary:* {summary}\n\n")
    
    if diff_text:
        display_diff = diff_text[:3000] + "..." if len(diff_text) > 3000 else diff_text
        msg += f"```diff\n{display_diff}\n```\n\n"
    
    markup = {
        "inline_keyboard": [[
            {"text": "✅ Approve", "callback_data": "approve"},
            {"text": "❌ Reject", "callback_data": "reject"}
        ]]
    }
    send_message(msg, reply_markup=markup)

def wait_for_verdict(timeout=300):
    """
    Polls for 'approve' or 'reject' callback data.
    """
    start_time = time.time()
    last_update_id = 0
    
    while time.time() - start_time < timeout:
        url = f"https://api.telegram.org/bot{TOKEN}/getUpdates?offset={last_update_id + 1}"
        try:
            import requests
            res = requests.get(url).json()
            if res["ok"] and res["result"]:
                for update in res["result"]:
                    last_update_id = update["update_id"]
                    
                    # Check both text messages AND callback queries
                    verdict = None
                    
                    if "callback_query" in update:
                        cb = update["callback_query"]
                        data = cb.get("data")
                        sender_id = str(cb.get("from", {}).get("id", ""))
                        if sender_id == CHAT_ID:
                            verdict = data
                    elif "message" in update:
                        msg = update["message"]
                        text = msg.get("text", "").strip().lower()
                        sender_id = str(msg.get("from", {}).get("id", ""))
                        if sender_id == CHAT_ID:
                            if text in ["approve", "ok", "yes"]: verdict = "approve"
                            if text in ["reject", "no", "cancel"]: verdict = "reject"

                    if verdict == "approve":
                        send_message("✅ *Change Approved via Button.* Applying now...")
                        return True
                    if verdict == "reject":
                        send_message("❌ *Change Rejected via Button.* Action aborted.")
                        return False
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(5)
    
    send_message("⏰ *Approval Timeout.* Action aborted.")
    return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", required=True)
    parser.add_argument("--summary", required=True)
    parser.add_argument("--diff", help="Text of the diff/change")
    args = parser.parse_args()

    send_diff_request(args.file, args.summary, args.diff)
    if wait_for_verdict():
        sys.exit(0) # Success -> Proceed
    else:
        sys.exit(1) # Failure -> Abort
