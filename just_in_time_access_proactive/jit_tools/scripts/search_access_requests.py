import sys

try:
    import sqlite3
except ImportError:
    # During discovery phase, sqlite3 might not be available
    pass

def search_access_requests(status=None, tool_name=None):
    conn = sqlite3.connect('/var/lib/database/access_requests.db')
    cursor = conn.cursor()

    query = "SELECT request_id, user_email, tool_name, ttl, status FROM requests WHERE 1=1"
    params = []

    if status:
        query += " AND status=?"
        params.append(status)
    if tool_name:
        query += " AND tool_name LIKE ?"
        params.append(f"%{tool_name}%")

    query += " ORDER BY request_id DESC"
    cursor.execute(query, params)
    rows = cursor.fetchall()

    if not rows:
        print("No matching access requests found.")
        return

    print("\n🔍 Search Results 🔍\n")
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
    status = sys.argv[1] if len(sys.argv) > 1 else None
    tool_name = sys.argv[2] if len(sys.argv) > 2 else None
    search_access_requests(status, tool_name) 