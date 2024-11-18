import sqlite3

def list_active_access_requests():
    conn = sqlite3.connect('/var/lib/database/access_requests.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT request_id, user_email, tool_name, tool_params, ttl, status
        FROM requests WHERE status='pending'
    ''')
    rows = cursor.fetchall()

    if not rows:
        print("🔍 No active access requests found at this time.")
        return

    print("\n🔐 Active Access Requests 🔐\n")

    for row in rows:
        request_id, user_email, tool_name, tool_params, ttl, status = row
        print("📝 Request Details:")
        print(f"🆔 Request ID: {request_id}")
        print(f"📧 User Email: {user_email}")
        print(f"🛠️  Tool Name: {tool_name}")
        print(f"⚙️  Parameters: {tool_params}")
        print(f"⏱️  Requested TTL: {ttl}")
        print(f"📊 Status: {status}")
        print("✨" + "─" * 38 + "✨\n")

    conn.close()

if __name__ == "__main__":
    list_active_access_requests() 