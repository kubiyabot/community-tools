import sys

try:
    import sqlite3
except ImportError:
    # During discovery phase, sqlite3 might not be available
    pass
def view_user_requests(user_email):
    conn = sqlite3.connect('/var/lib/database/access_requests.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT request_id, tool_name, tool_params, ttl, status
        FROM requests 
        WHERE user_email=?
        ORDER BY request_id DESC
    ''', (user_email,))
    rows = cursor.fetchall()

    if not rows:
        print(f"No access requests found for user {user_email}.")
        return

    print(f"\n🔐 Access Requests for {user_email} 🔐\n")
    for row in rows:
        request_id, tool_name, tool_params, ttl, status = row
        print(f"📝 Request {request_id}:")
        print(f"  🛠️  Tool: {tool_name}")
        print(f"  ⚙️  Parameters: {tool_params}")
        print(f"  ⏱️  TTL: {ttl}")
        print(f"  📊 Status: {status}")
        print("  " + "─" * 30)

    conn.close()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: view_user_requests.py <user_email>")
        sys.exit(1)

    user_email = sys.argv[1]
    view_user_requests(user_email) 