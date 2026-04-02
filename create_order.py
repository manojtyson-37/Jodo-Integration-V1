import os
import requests
from dotenv import load_dotenv
from notify import send_message

# Load environment variables
load_dotenv()

JODO_API_KEY = os.getenv("JODO_API_KEY")
JODO_API_SECRET = os.getenv("JODO_API_SECRET")
JODO_API_HOST = os.getenv("JODO_API_HOST", "ext.devtest1.jodopay.com")

def create_order(customer_data):
    """
    Creates an order in Jodo system using the provided customer data.
    """
    url = f"https://{JODO_API_HOST}/api/v1/integrations/pay/orders"
    auth = (JODO_API_KEY, JODO_API_SECRET)
    
    # Payload based on Postman collection
    payload = {
        "name": customer_data.get("name"),
        "phone": customer_data.get("phone"),
        "email": customer_data.get("email"),
        "details": [
            {
                "component_type": "Payable Amount",
                "amount": customer_data.get("amount", 0)
            }
        ],
        "callback_url": customer_data.get("callback_url", "https://example.com/order-status")
    }

    print(f"Creating order for {customer_data['name']}...")
    try:
        response = requests.post(url, json=payload, auth=auth)
        if response.status_code != 200 and response.status_code != 201:
            print(f"Error Response Body: {response.text}")
        response.raise_for_status()
        order_data = response.json()
        
        # Notify via Telegram
        msg = (f"📦 *Order Created Successfully!*\n\n"
               f"Account: {customer_data['name']}\n"
               f"Amount: ₹{customer_data['amount']}\n"
               f"Order ID: `{order_data.get('id', 'N/A')}`")
        send_message(msg)
        
        return order_data
    except Exception as e:
        error_msg = f"❌ *Order Creation Failed!*\n\nError: {str(e)}"
        send_message(error_msg)
        print(error_msg)
        return None

if __name__ == "__main__":
    # Test Data
    test_customer = {
        "name": "Manoj Prototype",
        "phone": "9876543210",
        "email": "manoj@example.com",
        "amount": 1.0, # Test amount
        "callback_url": "https://webhook.site/test"
    }
    
    if not JODO_API_KEY or not JODO_API_SECRET:
        print("Error: JODO_API_KEY or JODO_API_SECRET not set in .env")
    else:
        result = create_order(test_customer)
        if result:
            print(f"Order Success: {result}")
