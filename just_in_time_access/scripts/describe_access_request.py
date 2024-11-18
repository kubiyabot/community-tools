import sys
import sqlite3

def describe_access_request(request_id):
    conn = sqlite3.connect('/var/lib/database/access_requests.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT request_id, user_email, tool_name, tool_params, ttl, status
        FROM requests WHERE request_id=?
    ''', (request_id,))
    row = cursor.fetchone()

    if row is None:
        print(f"🔍 No access request found with Request ID {request_id}.")
        return

    request_id, user_email, tool_name, tool_params, ttl, status = row
    
    print("\n🔐 Access Request Details 🔐\n")
    print("📝 Request Information:")
    print(f"🆔 Request ID: {request_id}")
    print(f"📧 User Email: {user_email}")
    print(f"🛠️  Tool Name: {tool_name}")
    print(f"⚙️  Parameters: {tool_params}")
    print(f"⏱️  Requested TTL: {ttl}")
    print(f"📊 Status: {status}")
    print("\n✨" + "─" * 38 + "✨")

    conn.close()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("❌ Usage: describe_access_request.py <request_id>")
        sys.exit(1)

    request_id = sys.argv[1]
    describe_access_request(request_id) 