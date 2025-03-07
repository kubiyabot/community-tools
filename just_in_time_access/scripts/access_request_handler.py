import os
import sys
import requests

try:
    import requests
except ImportError:
    # During discovery phase, requests might not be available
    pass


def get_requested_tool_and_params(
    request_id: str, enforcer_base_url: str
) -> tuple[str, dict]:
    response = requests.get(f"{enforcer_base_url}/requests/describe/{request_id}")
    if response.status_code >= 400:
        print(f"Failed to fetch request details: {response.text}")
        sys.exit(1)

    request_details = response.json()
    tool_name = request_details["request"]["tool"]["name"]
    params = request_details["request"]["tool"]["parameters"]
    return tool_name, params


def send_approval_request(request_id: str, ttl: str):
    enforcer_base_url = "http://enforcer.kubiya:5001"
    req_tool_name, req_tool_params = get_requested_tool_and_params(
        request_id, enforcer_base_url
    )
    user_email = os.environ["KUBIYA_USER_EMAIL"]

    # Send webhook to Kubiya API
    payload = {
        "request_id": request_id,
        "user_email": user_email,
        "tool_name": req_tool_name,
        "tool_params": req_tool_params,
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
