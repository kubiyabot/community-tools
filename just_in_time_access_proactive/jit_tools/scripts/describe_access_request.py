import sys

try:
    import requests
except ImportError:
    # During discovery phase, sqlite3 might not be available
    pass


def describe_access_request(request_id):
    res = requests.get(f"http://enforcer.kubiya:5001/requests/describe/{request_id}")
    if res.status_code >= 400:
        print(f"Failed to fetch request details: {res.text}")
        sys.exit(1)

    request_details = res.json()
    print(f"event details: {request_details}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("❌ Usage: describe_access_request.py <request_id>")
        sys.exit(1)

    request_id = sys.argv[1]
    describe_access_request(request_id)
