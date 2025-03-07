import sys

try:
    import requests
except ImportError:
    # During discovery phase, sqlite3 might not be available
    pass


def list_active_requests():
    res = requests.get("http://enforcer.kubiya:5001/requests/list")
    if res.status_code >= 400:
        print(f"Failed to fetch active requests: {res.text}")
        sys.exit(1)
    active_requests = res.json()
    if not active_requests:
        print("No active access requests found.")
        return

    print(active_requests)


if __name__ == "__main__":
    list_active_requests()
