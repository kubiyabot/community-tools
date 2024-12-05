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
        
        # Format and print the filtered results
        for req in user_requests:
            print("\n" + "-" * 50)
            print(f"Request ID: {req['id']}")
            print(f"User Email: {req['request']['user']['email']}")
            print(f"Tool: {req['request']['tool']['name']}")
            print(f"Status: {'Approved' if req['approved'] else 'Pending'}")
            print(f"Created At: {req['created_at']}")
            if req.get('ttl') and req['ttl'] != '0001-01-01T00:00:00Z':
                print(f"TTL: {req['ttl']}")

    except requests.RequestException as e:
        print(f"Failed to fetch requests: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    view_user_requests()