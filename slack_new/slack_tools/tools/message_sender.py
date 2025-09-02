"""
Slack Message Sender Tool - Send messages to channels using channel ID
"""
from kubiya_sdk.tools import Arg, Tool, FileSpec
from kubiya_sdk.tools.registry import tool_registry

SLACK_ICON_URL = "https://a.slack-edge.com/80588/marketing/img/icons/icon_slack_hash_colored.png"

# Send Message Tool
send_message_tool = Tool(
    name="slack_send_message", 
    description="Send message to Slack channel using channel ID. Use slack_find_channel_by_name first to get the channel ID",
    type="docker",
    image="python:3.11-slim",
    icon_url=SLACK_ICON_URL,
    content="""
pip install --no-cache-dir --quiet requests
python3 /tmp/send_message.py
""",
    with_files=[
        FileSpec(
            destination="/tmp/send_message.py",
            content="""
import os
import sys
import requests
from typing import Optional

def send_slack_message():
    channel = os.getenv('channel')
    message = os.getenv('message')
    thread_ts = os.getenv('thread_ts')
    
    if not channel:
        print("❌ Missing channel")
        return False
    if not message:
        print("❌ Missing message")
        return False
    
    # Get token
    try:
        resp = requests.get(
            "https://api.kubiya.ai/api/v1/integration/slack/token/1",
            headers={"Authorization": f"UserKey {os.getenv('KUBIYA_API_KEY')}"},
            timeout=10
        )
        token = resp.json().get('token') if resp.status_code == 200 else None
        if not token:
            print("❌ No token")
            return False
        print(f"🔑 Token: {token[:10]}...")
    except Exception as e:
        print(f"❌ Token failed: {e}")
        return False
    
    # Try to join channel (non-blocking)
    try:
        requests.post(
            "https://slack.com/api/conversations.join",
            headers={"Authorization": f"Bearer {token}"},
            json={"channel": channel},
            timeout=5
        )
    except:
        pass  # Ignore join errors
    
    # Send message
    payload = {"channel": channel, "text": message}
    if thread_ts:
        payload["thread_ts"] = thread_ts
    
    print(f"📤 Sending to channel: {channel}")
    
    try:
        resp = requests.post(
            "https://slack.com/api/chat.postMessage",
            headers={"Authorization": f"Bearer {token}"},
            json=payload,
            timeout=10
        )
        result = resp.json() if resp.status_code == 200 else {}
        print(f"📋 Full response: {result}")
        if result.get('ok'):
            ts = result.get('ts', 'unknown')
            print(f"✅ Sent - Message timestamp: {ts}")
            return True
        else:
            print(f"❌ {result.get('error', 'failed')}")
            return False
    except Exception as e:
        print(f"❌ {e}")
        return False

if __name__ == "__main__":
    success = send_slack_message()
    if not success:
        sys.exit(1)
"""
        )
    ],
    args=[
        Arg(name="channel", type="str", description="Channel ID (use slack_find_channel_by_name to get ID first)", required=True),
        Arg(name="message", type="str", description="Message text to send (supports Slack markdown)", required=True),
        Arg(name="thread_ts", type="str", description="Thread timestamp for replies (optional)", required=False),
    ],
    secrets=["KUBIYA_API_KEY"]
)

# Register the tool
tool_registry.register("slack", send_message_tool)