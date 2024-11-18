import sys
import os
import json
import requests
import sqlite3
import uuid

def send_approval_request(tool_name, user_email, tool_params, ttl):
    database_path = '/var/lib/database/access_requests.db'
    request_id = str(uuid.uuid4())

    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS requests (
            request_id TEXT PRIMARY KEY,
            user_email TEXT,
            tool_name TEXT,
            tool_params TEXT,
            ttl TEXT,
            status TEXT
        )
    ''')

    cursor.execute('''
        INSERT INTO requests (request_id, user_email, tool_name, tool_params, ttl, status)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (request_id, user_email, tool_name, tool_params, ttl, 'pending'))

    conn.commit()
    conn.close()

    # Send webhook to Kubiya API
    kubiya_api_url = os.getenv('KUBIYA_API_URL')
    payload = {
        "request_id": request_id,
        "user_email": user_email,
        "tool_name": tool_name,
        "tool_params": tool_params,
        "ttl": ttl,
        "status": "pending"
    }

    response = requests.post(kubiya_api_url, json=payload)

    if response.status_code != 200:
        print(f"Failed to send approval request: {response.text}")
        sys.exit(1)

if __name__ == "__main__":
    tool_name = sys.argv[1]
    user_email = sys.argv[2]
    tool_params = sys.argv[3]
    ttl = sys.argv[4] if len(sys.argv) > 4 else "1h"

    send_approval_request(tool_name, user_email, tool_params, ttl)