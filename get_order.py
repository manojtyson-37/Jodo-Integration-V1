import os
import requests
from dotenv import load_dotenv
from notify import send_message

# Load environment variables
load_dotenv()

JODO_API_KEY = os.getenv("JODO_API_KEY")
JODO_API_SECRET = os.getenv("JODO_API_SECRET")
JODO_API_HOST = os.getenv("JODO_API_HOST", "ext.devtest1.jodopay.com")

def get_order_details(order_id):
    """
    Fetches the details of a Jodo order by its ID.
    """
    url = f"https://{JODO_API_HOST}/api/v1/integrations/pay/orders/{order_id}"
    auth = (JODO_API_KEY, JODO_API_SECRET)
    
    print(f"Fetching details for Order ID: {order_id}...")
    try:
        response = requests.get(url, auth=auth)
        if response.status_code != 200:
            print(f"Error Response Body: {response.text}")
        response.raise_for_status()
        order_data = response.json()
        
        # Notify via Telegram
        status = order_data.get('status', 'Unknown')
        msg = (f"🔍 *Order Details Retreived!*\n\n"
               f"Order ID: `{order_id[:10]}...`\n"
               f"Status: *{status.upper()}*\n"
               f"Amount: ₹{order_data.get('amount', 'N/A')}")
        send_message(msg)
        
        return order_data
    except Exception as e:
        error_msg = f"❌ *Failed to fetch order details!*\n\nError: {str(e)}"
        send_message(error_msg)
        print(error_msg)
        return None

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        res = get_order_details(sys.argv[1])
        if res:
            print(f"Order Details: {res}")
    else:
        print("Usage: python3 get_order.py <order_id>")
