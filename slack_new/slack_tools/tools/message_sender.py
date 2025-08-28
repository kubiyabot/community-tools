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

class SlackSendMessage:
    def __init__(self):
        self.kubiya_token = None
    
    def get_kubiya_slack_token(self) -> Optional[str]:
        try:
            print("🔐 Retrieving Slack token from Kubiya integration API...")
            response = requests.get(
                "https://api.kubiya.ai/api/v1/integration/slack/token/1",
                headers={"Authorization": f"UserKey {os.getenv('KUBIYA_API_KEY')}"},
                timeout=30
            )
            
            print(f"📡 API Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                token = data.get('token')
                if token and token != 'null':
                    self.kubiya_token = token
                    print("✅ Successfully retrieved Slack token from Kubiya API")
                    return token
                else:
                    print("❌ Token is null or missing in API response")
                    return None
            else:
                print(f"❌ Failed to get Kubiya Slack token: HTTP {response.status_code}")
                print(f"📄 Response: {response.text}")
                return None
            
        except Exception as e:
            print(f"💥 Error getting Kubiya Slack token: {e}")
            return None
    
    def make_slack_request(self, endpoint: str, token: str, data: dict) -> Optional[dict]:
        url = f"https://slack.com/api/{endpoint}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        print(f"🚀 Making Slack API request to: {endpoint}")
        print(f"📦 Payload: {data}")
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=30)
            print(f"📡 Slack API Response Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    print("✅ Slack API request successful")
                    return result
                else:
                    error_msg = result.get('error', 'unknown')
                    print(f"❌ Slack API error: {error_msg}")
                    return None
            else:
                print(f"❌ HTTP error {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            print(f"💥 Request error: {e}")
            return None
    
    def send_message(self, channel: str, message: str, thread_ts: Optional[str] = None) -> bool:
        print("🚀 Starting Slack message send process...")
        print(f"🎯 Target channel: {channel}")
        print(f"💬 Message: '{message[:100]}{'...' if len(message) > 100 else ''}'")
        if thread_ts:
            print(f"🧵 Thread reply to: {thread_ts}")
        
        kubiya_token = self.get_kubiya_slack_token()
        if not kubiya_token:
            print("❌ Failed to get Kubiya Slack token for message posting")
            return False
        
        if not channel.startswith(('C', 'D', 'G')):
            print(f"❌ Channel '{channel}' doesn't look like a valid channel ID.")
            print("💡 Use slack_find_channel_by_name tool first to get the channel ID:")
            print(f"   Example: slack_find_channel_by_name --channel_name '{channel.lstrip('#')}'")
            return False
        
        post_data = {
            "channel": channel,
            "text": message
        }
        
        if thread_ts:
            post_data["thread_ts"] = thread_ts
        
        print(f"📤 Sending message to Slack channel {channel}...")
        result = self.make_slack_request("chat.postMessage", kubiya_token, post_data)
        
        if result:
            message_ts = result.get('ts', 'unknown')
            print(f"🎉 Message sent successfully!")
            print(f"📌 Message timestamp: {message_ts}")
            print(f"🔗 Channel: {channel}")
            return True
        else:
            print("❌ Failed to send message")
            return False

if __name__ == "__main__":
    print("=" * 60)
    print("📬 SLACK MESSAGE SENDER TOOL")
    print("=" * 60)
    
    channel = os.getenv('channel')
    message = os.getenv('message')
    thread_ts = os.getenv('thread_ts')
    
    print("📋 Input Parameters:")
    print(f"   • Channel: {channel}")
    print(f"   • Message Length: {len(message) if message else 0} characters")
    print(f"   • Thread Reply: {'Yes' if thread_ts else 'No'}")
    
    if not channel:
        print("❌ Missing channel parameter")
        sys.exit(1)
    if not message:
        print("❌ Missing message parameter")
        sys.exit(1)
        
    print("\n🔄 Initializing Slack message sender...")
    sender = SlackSendMessage()
    success = sender.send_message(channel, message, thread_ts)

    print("\n" + "=" * 60)
    if success:
        print("✅ OPERATION COMPLETED SUCCESSFULLY")
    else:
        print("❌ OPERATION FAILED")
        sys.exit(1)
    print("=" * 60)
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