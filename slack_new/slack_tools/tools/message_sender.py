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
        self.bot_user_id = None
    
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
    
    def get_bot_user_id(self) -> Optional[str]:
        if not self.kubiya_token:
            print("❌ No Kubiya token available for bot ID lookup")
            return None
        
        try:
            print("🤖 Getting bot user ID...")
            response = requests.get(
                "https://slack.com/api/auth.test",
                headers={"Authorization": f"Bearer {self.kubiya_token}"},
                timeout=30
            )
            
            print(f"📡 Auth test response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    self.bot_user_id = data.get('user_id')
                    bot_name = data.get('user', 'Unknown')
                    print(f"✅ Bot user ID: {self.bot_user_id} ({bot_name})")
                    return self.bot_user_id
                else:
                    print(f"❌ Auth test failed: {data.get('error')}")
                    return None
            else:
                print(f"❌ HTTP error {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            print(f"💥 Error getting bot user ID: {e}")
            return None
    
    def join_channel(self, channel: str) -> bool:
        if not self.kubiya_token or not self.bot_user_id:
            print("❌ Missing token or bot user ID for channel join")
            return False
        
        try:
            print(f"🔍 Checking if bot is already in channel {channel}...")
            
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
                        print("✅ Bot is already a member of the channel")
                        return True
                    else:
                        print("➕ Bot not in channel, attempting to join...")
                else:
                    print(f"⚠️ Could not check channel membership: {data.get('error')}")
            
            print(f"🚪 Inviting bot to channel {channel}...")
            invite_response = requests.post(
                "https://slack.com/api/conversations.invite",
                headers={"Authorization": f"Bearer {self.kubiya_token}"},
                json={"channel": channel, "users": self.bot_user_id},
                timeout=30
            )
            
            print(f"📡 Invite response status: {invite_response.status_code}")
            
            if invite_response.status_code == 200:
                invite_data = invite_response.json()
                if invite_data.get('ok'):
                    print("✅ Successfully joined channel")
                    return True
                else:
                    error = invite_data.get('error', 'unknown')
                    if error == 'already_in_channel':
                        print("✅ Bot is already in the channel")
                        return True
                    elif error == 'channel_not_found':
                        print("❌ Channel not found")
                        return False
                    else:
                        print(f"⚠️ Failed to join channel: {error} (continuing anyway)")
                        return True
            else:
                print(f"❌ HTTP error {invite_response.status_code}: {invite_response.text}")
                return True
                
        except Exception as e:
            print(f"💥 Error joining channel: {e} (continuing anyway)")
            return True
    
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
        
        bot_user_id = self.get_bot_user_id()
        if not bot_user_id:
            print("⚠️ Could not get bot user ID, proceeding without channel join")
        
        if bot_user_id:
            join_success = self.join_channel(channel)
            if not join_success:
                print("⚠️ Failed to join channel, but will attempt to send message anyway")
        
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
        
    print("\\n🔄 Initializing Slack message sender...")
    sender = SlackSendMessage()
    success = sender.send_message(channel, message, thread_ts)

    print("\\n" + "=" * 60)
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