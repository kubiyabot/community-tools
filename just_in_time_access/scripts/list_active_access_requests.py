import sys

try:
    import sqlite3
except ImportError:
    # During discovery phase, sqlite3 might not be available
    pass

def list_active_requests():
    conn = sqlite3.connect('/var/lib/database/access_requests.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT request_id, user_email, tool_name, ttl, status
        FROM requests 
        WHERE status='pending' OR status='approved'
        ORDER BY request_id
    ''')
    rows = cursor.fetchall()

    if not rows:
        print("No active access requests found.")
        return

    print("\n🔐 Active Access Requests 🔐\n")
    for row in rows:
        request_id, user_email, tool_name, ttl, status = row
        print(f"📝 Request {request_id}:")
        print(f"  📧 User: {user_email}")
        print(f"  🛠️  Tool: {tool_name}")
        print(f"  ⏱️  TTL: {ttl}")
        print(f"  📊 Status: {status}")
        print("  " + "─" * 30)

    conn.close()

if __name__ == "__main__":
    list_active_requests() 