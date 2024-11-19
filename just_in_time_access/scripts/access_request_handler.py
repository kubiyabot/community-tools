import os
import sys
import requests

try:
    import requests
except ImportError:
    # During discovery phase, requests might not be available
    pass


def send_approval_request(request_id: str, ttl: str):
    user_email = os.environ["KUBIYA_USER_EMAIL"]
    kubiya_tool_name = ["KUBIYA_TOOL_NAME"]
    kubiya_tool_params = os.environ["KUBIYA_TOOL_PARAMS"]

    # Send webhook to Kubiya API
    payload = {
        "request_id": request_id,
        "user_email": user_email,
        "tool_name": kubiya_tool_name,
        "tool_params": kubiya_tool_params,
        "requested_ttl": ttl,
        "status": "pending",
    }

    kubiya_api_url = os.environ["REQUEST_ACCESS_WEBHOOK_URL"]
    response = requests.post(kubiya_api_url, json=payload)

    if response.status_code >= 400:
        print(f"Failed to send approval request: {response.text}")
        sys.exit(1)

    print("Approval request sent successfully.")


if __name__ == "__main__":
    request_id = sys.argv[1]
    ttl = sys.argv[2] if len(sys.argv) > 2 else "1h"

    send_approval_request(request_id=request_id, ttl=ttl)
