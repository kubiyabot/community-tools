"""
Slack Channel Finder Tool - Find channel ID by name using high-tier token
"""
from kubiya_sdk.tools import Arg, Tool, FileSpec
from kubiya_sdk.tools.registry import tool_registry

SLACK_ICON_URL = "https://a.slack-edge.com/80588/marketing/img/icons/icon_slack_hash_colored.png"

# Find Channel Tool
find_channel_tool = Tool(
    name="slack_find_channel_by_name", 
    description="Find Slack channel ID by name using high-tier token. Searches across public, private channels and DMs",
    type="docker",
    image="python:3.11-slim",
    icon_url=SLACK_ICON_URL,
    content="""
pip install --no-cache-dir --quiet requests
python3 /tmp/find_channel.py
""",
    with_files=[
        FileSpec(
            destination="/tmp/find_channel.py",
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
        token = os.getenv('slack_app_token')
        if token and token != 'null':
            self.slack_app_token = token
            return token
        else:
            print("❌ Missing slack_app_token environment variable")
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
            print("❌ Failed to get Slack app token for channel discovery")
            return None
        
        clean_name = channel_name.lstrip('#')
        channel_types = [
            "public_channel,private_channel",
            "public_channel",
            "private_channel", 
            "im,mpim"
        ]
        
        for types in channel_types:
            channel_id = self._search_channels_by_type(app_token, types, clean_name)
            if channel_id:
                print(f"Channel ID: {channel_id}")
                return channel_id
            time.sleep(1)
        
        print(f"❌ Channel '{clean_name}' not found")
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
            
            for channel in channels:
                if channel.get('name') == target_name:
                    return channel.get('id')
            
            cursor = result.get('response_metadata', {}).get('next_cursor')
            if not cursor:
                break
                
            time.sleep(1)
        
        return None

if __name__ == "__main__":
    channel_name = os.getenv('channel_name')
    if not channel_name:
        print("❌ Missing channel_name parameter")
        sys.exit(1)
        
    finder = SlackChannelFinder()
    result = finder.find_channel_by_name(channel_name)

    if result:
        print(f"Channel ID: {result}")
    else:
        print("Channel not found")
        sys.exit(1)
"""
        )
    ],
    args=[
        Arg(name="channel_name", type="str", description="Channel name to search for (with or without # prefix)", required=True),
    ],
    secrets=["slack_app_token"]
)

# Register the tool
tool_registry.register("slack", find_channel_tool)