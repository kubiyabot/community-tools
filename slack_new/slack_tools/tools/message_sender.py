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
        self.slack_app_token = None
        self.bot_user_id = None
    
    def get_kubiya_slack_token(self) -> Optional[str]:
        try:
            response = requests.get(
                "https://api.kubiya.ai/api/v1/integration/slack/token/1",
                headers={"Authorization": f"UserKey {os.getenv('KUBIYA_API_KEY')}"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                token = data.get('token')
                if token and token != 'null':
                    self.kubiya_token = token
                    return token
            
            print(f"❌ Failed to get Slack token: {response.status_code}")
            return None
            
        except Exception as e:
            print(f"❌ Error getting Slack token: {e}")
            return None
    
    def get_slack_app_token(self) -> Optional[str]:
        token = os.getenv('slack_app_token')
        if token and token != 'null':
            self.slack_app_token = token
            return token
        return None
    
    def get_bot_user_id(self) -> Optional[str]:
        if not self.kubiya_token:
            return None
        
        try:
            response = requests.get(
                "https://slack.com/api/auth.test",
                headers={"Authorization": f"Bearer {self.kubiya_token}"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    self.bot_user_id = data.get('user_id')
                    return self.bot_user_id
            return None
                
        except Exception:
            return None
    
    def join_channel(self, channel: str) -> bool:
        if not self.kubiya_token or not self.bot_user_id:
            return False
        
        try:
            # Check if bot is already in channel
            response = requests.get(
                f"https://slack.com/api/conversations.members?channel={channel}",
                headers={"Authorization": f"Bearer {self.kubiya_token}"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    members = data.get('members', [])
                    if self.bot_user_id in members:
                        return True
            
            # Try to join channel
            invite_response = requests.post(
                "https://slack.com/api/conversations.invite",
                headers={"Authorization": f"Bearer {self.kubiya_token}"},
                json={"channel": channel, "users": self.bot_user_id},
                timeout=30
            )
            
            if invite_response.status_code == 200:
                invite_data = invite_response.json()
                if invite_data.get('ok') or invite_data.get('error') == 'already_in_channel':
                    return True
            
            return True  # Continue anyway
                
        except Exception:
            return True  # Continue anyway
    
    def make_slack_request(self, endpoint: str, token: str, data: dict) -> Optional[dict]:
        url = f"https://slack.com/api/{endpoint}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    return result
                else:
                    error_msg = result.get('error', 'unknown')
                    print(f"❌ Slack API error: {error_msg}")
                    return None
            else:
                print(f"❌ HTTP error {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Request error: {e}")
            return None
    
    def send_message(self, channel: str, message: str, thread_ts: Optional[str] = None) -> bool:
        kubiya_token = self.get_kubiya_slack_token()
        if not kubiya_token:
            print("❌ Failed to get Slack token")
            return False
        
        # Try to join channel first
        bot_user_id = self.get_bot_user_id()
        if bot_user_id:
            self.join_channel(channel)
        
        # Check if this looks like a channel name instead of ID
        if not channel.startswith(('C', 'D', 'G')):
            print(f"❌ Invalid channel ID format: '{channel}'")
            print(f"🔍 Channel IDs should start with C (public), D (DM), or G (private). Use slack_find_channel_by_name to get the correct ID.")
            return False
        elif channel.startswith('#') or any(char in channel for char in ['-', '_', ' ']) or (len(channel) > 3 and channel[1:].islower()):
            # This looks like a channel name, not an ID
            print(f"❌ This tool accepts only channel IDs (starting with C, D, or G), not channel names.")
            print(f"📋 Channel provided: '{channel}'")
            print(f"🔍 Please use 'slack_find_channel_by_name' first to get the channel ID, then use that ID here.")
            print(f"💡 Example: slack_find_channel_by_name channel_name=\"{channel.lstrip('#')}\"")
            return False
        
        post_data = {
            "channel": channel,
            "text": message
        }
        
        if thread_ts:
            post_data["thread_ts"] = thread_ts
        
        result = self.make_slack_request("chat.postMessage", kubiya_token, post_data)
        
        if result:
            print("✅ Message sent successfully")
            return True
        else:
            return False

if __name__ == "__main__":
    channel = os.getenv('channel')
    message = os.getenv('message')
    thread_ts = os.getenv('thread_ts')
    
    if not channel:
        print("❌ Missing channel parameter")
        sys.exit(1)
    if not message:
        print("❌ Missing message parameter")
        sys.exit(1)
        
    sender = SlackSendMessage()
    success = sender.send_message(channel, message, thread_ts)

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