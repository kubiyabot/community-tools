"""
Slack Tools Module - Tool Definitions for Dual Token Slack Integration
"""
from kubiya_sdk.tools import Arg
from kubiya_sdk.tools.registry import tool_registry
from .base import SlackBase

# Python-based tools using Kubiya SDK
from kubiya_sdk.tools import PythonTool

# Find Channel Tool
find_channel_tool = PythonTool(
    name="slack_find_channel_by_name",
    description="Find Slack channel ID by name using high-tier token. Searches across public, private channels and DMs",
    content="""
import os
import sys
import time
import requests
from typing import Optional

class SlackChannelFinder:
    def __init__(self):
        self.slack_app_token = None
    
    def get_slack_app_token(self) -> Optional[str]:
        try:
            response = requests.get(
                "https://api.kubiya.ai/api/v1/secret/get_secret_value/slack_app_token",
                headers={"Authorization": f"Bearer {os.getenv('KUBIYA_API_TOKEN')}"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                token = data.get('value') or data.get('secret_value') or data.get('token')
                if token and token != 'null':
                    self.slack_app_token = token
                    return token
            
            print(f"Failed to get Slack app token: {response.status_code}")
            return None
            
        except Exception as e:
            print(f"Error getting Slack app token: {e}")
            return None
    
    def make_slack_request(self, endpoint: str, token: str) -> Optional[dict]:
        url = f"https://slack.com/api/{endpoint}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    return result
                else:
                    print(f"Slack API error: {result.get('error')}")
                    return None
            elif response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 1))
                print(f"Rate limited. Retry after {retry_after} seconds")
                return None
            else:
                print(f"HTTP error {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            print(f"Request error: {e}")
            return None
    
    def find_channel_by_name(self, channel_name: str) -> Optional[str]:
        app_token = self.get_slack_app_token()
        if not app_token:
            print("L Failed to get Slack app token for channel discovery")
            return None
        
        clean_name = channel_name.lstrip('#')
        print(f"= Searching for channel: '{clean_name}'")
        
        channel_types = [
            ("public_channel,private_channel", "public and private channels"),
            ("public_channel", "public channels only"),
            ("private_channel", "private channels only"), 
            ("im,mpim", "direct messages and group DMs")
        ]
        
        for types, description in channel_types:
            print(f"= Searching {description}...")
            
            channel_id = self._search_channels_by_type(app_token, types, clean_name)
            if channel_id:
                print(f" Found channel ID: {channel_id}")
                return channel_id
            
            time.sleep(1)
        
        print(f"L Channel '{clean_name}' not found")
        return None
    
    def _search_channels_by_type(self, token: str, channel_types: str, target_name: str) -> Optional[str]:
        cursor = ""
        
        while True:
            endpoint = f"conversations.list?types={channel_types}&limit=1000"
            if cursor:
                endpoint += f"&cursor={cursor}"
            
            result = self.make_slack_request(endpoint, token)
            if not result:
                break
            
            channels = result.get('channels', [])
            print(f"=� Checking {len(channels)} channels...")
            
            for channel in channels:
                if channel.get('name') == target_name:
                    return channel.get('id')
            
            cursor = result.get('response_metadata', {}).get('next_cursor')
            if not cursor:
                break
                
            time.sleep(1)
        
        return None

finder = SlackChannelFinder()
result = finder.find_channel_by_name(channel_name)

if result:
    print(f"Channel ID: {result}")
else:
    print("Channel not found")
    sys.exit(1)
""",
    args=[
        Arg(name="channel_name", type="str", description="Channel name to search for (with or without # prefix)", required=True),
    ],
    requirements=["requests>=2.31.0"]
)

# Send Message Tool
send_message_tool = PythonTool(
    name="slack_send_message",
    description="Send message to Slack channel using channel ID. Use slack_find_channel_by_name first to get the channel ID",
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
            response = requests.get(
                "https://api.kubiya.ai/api/v1/integration/slack/token/1",
                headers={"Authorization": f"Bearer {os.getenv('KUBIYA_API_TOKEN')}"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                token = data.get('token')
                if token and token != 'null':
                    self.kubiya_token = token
                    return token
            
            print(f"Failed to get Kubiya Slack token: {response.status_code}")
            return None
            
        except Exception as e:
            print(f"Error getting Kubiya Slack token: {e}")
            return None
    
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
                    print(f"Slack API error: {result.get('error')}")
                    return None
            else:
                print(f"HTTP error {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            print(f"Request error: {e}")
            return None
    
    def send_message(self, channel: str, message: str, thread_ts: Optional[str] = None) -> bool:
        kubiya_token = self.get_kubiya_slack_token()
        if not kubiya_token:
            print("L Failed to get Kubiya Slack token for message posting")
            return False
        
        if not channel.startswith(('C', 'D', 'G')):
            print(f"L Channel '{channel}' doesn't look like a valid channel ID.")
            print("=� Use slack_find_channel_by_name tool first to get the channel ID:")
            print(f"   Example: slack_find_channel_by_name --channel_name '{channel.lstrip('#')}'")
            return False
        
        post_data = {
            "channel": channel,
            "text": message
        }
        
        if thread_ts:
            post_data["thread_ts"] = thread_ts
        
        print(f"=� Sending message to channel {channel}...")
        result = self.make_slack_request("chat.postMessage", kubiya_token, post_data)
        
        if result:
            print(" Message sent successfully!")
            return True
        else:
            print("L Failed to send message")
            return False

sender = SlackSendMessage()
success = sender.send_message(channel, message, thread_ts)

if not success:
    sys.exit(1)
""",
    args=[
        Arg(name="channel", type="str", description="Channel ID (use slack_find_channel_by_name to get ID first)", required=True),
        Arg(name="message", type="str", description="Message text to send (supports Slack markdown)", required=True),
        Arg(name="thread_ts", type="str", description="Thread timestamp for replies (optional)", required=False),
    ],
    requirements=["requests>=2.31.0"]
)

# Register all tools
for tool in [
    find_channel_tool,
    send_message_tool,
]:
    tool_registry.register("slack_new", tool)