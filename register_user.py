import os
import requests
from dotenv import load_dotenv
from notify import send_message

# Load environment variables
load_dotenv()

JODO_API_KEY = os.getenv("JODO_API_KEY")
JODO_API_SECRET = os.getenv("JODO_API_SECRET")
JODO_API_HOST = os.getenv("JODO_API_HOST", "ext.devtest1.jodopay.com")

def register_user(user_data):
    """
    Registers a user in Jodo system.
    """
    url = f"https://{JODO_API_HOST}/api/v1/integrations/erp/users/register"
    auth = (JODO_API_KEY, JODO_API_SECRET)
    
    payload = {
        "name": user_data.get("name"),
        "phone": user_data.get("phone"),
        "email": user_data.get("email")
    }

    print(f"Registering user {user_data['name']}...")
    try:
        response = requests.post(url, json=payload, auth=auth)
        if response.status_code != 200 and response.status_code != 201:
            print(f"Error Response Body: {response.text}")
        response.raise_for_status()
        result = response.json()
        
        # Notify via Telegram
        msg = (f"👤 *User Registered Successfully!*\n\n"
               f"Name: {user_data['name']}\n"
               f"Registration ID: `{result.get('id', 'N/A')}`")
        send_message(msg)
        
        return result
    except Exception as e:
        error_msg = f"❌ *User Registration Failed!*\n\nError: {str(e)}"
        send_message(error_msg)
        print(error_msg)
        return None

if __name__ == "__main__":
    test_user = {
        "name": "Manoj User",
        "phone": "9876543210",
        "email": "manoj_user@example.com"
    }
    
    if not JODO_API_KEY or not JODO_API_SECRET:
        print("Error: JODO_API_KEY or JODO_API_SECRET not set in .env")
    else:
        result = register_user(test_user)
        if result:
            print(f"Registration Success: {result}")
