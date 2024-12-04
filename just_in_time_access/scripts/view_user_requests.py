import sys
import os
try:
    import requests
except ImportError:
    print("requests library not found. Please install it using 'pip install requests'")
    sys.exit(1)

def view_user_requests():
    # Get user email from environment variable
    user_email = os.getenv('KUBIYA_USER_EMAIL')
    if not user_email:
        print("Error: KUBIYA_USER_EMAIL environment variable not set")
        sys.exit(1)

    try:
        res = requests.get("http://enforcer.kubiya:5001/requests/list")
        res.raise_for_status()
        
        all_requests = res.json()
        if not all_requests:
            print("No requests found.")
            return

        # Filter requests for the specific user
        user_requests = [
            req for req in all_requests 
            if req.get('request', {}).get('user', {}).get('email') == user_email
        ]
        
        if not user_requests:
            print(f"No requests found for user: {user_email}")
            return
        
        print(user_requests)  # This will print the JSON objects as-is
        
    except requests.RequestException as e:
        print(f"Failed to fetch requests: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    view_user_requests()
