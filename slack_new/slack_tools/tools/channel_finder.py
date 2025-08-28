"""
Slack Channel Finder Tool - Find channel ID by name using high-tier token
"""
from kubiya_sdk.tools import Arg, Tool, FileSpec
from kubiya_sdk.tools.registry import tool_registry

SLACK_ICON_URL = "https://a.slack-edge.com/80588/marketing/img/icons/icon_slack_hash_colored.png"

# Python script content as a separate variable to avoid nested triple quotes
FIND_CHANNEL_SCRIPT = '''
import os
import sys
import time
import requests
from typing import Optional, List, Tuple
import re

class SlackChannelFinder:
    def __init__(self):
        self.slack_app_token = None
    
    def normalize_channel_name(self, name: str) -> str:
        """Normalize channel name by removing special chars and converting to lowercase"""
        # First remove # prefix if present
        clean_name = name.lstrip('#')
        # Then remove all non-alphanumeric chars and convert to lowercase
        return re.sub(r'[^a-z0-9]', '', clean_name.lower())
    
    def calculate_fuzzy_score(self, target: str, candidate: str) -> float:
        """Calculate fuzzy match score between target and candidate channel names"""
        target_norm = self.normalize_channel_name(target)
        candidate_norm = self.normalize_channel_name(candidate)
        
        # Exact match (normalized)
        if target_norm == candidate_norm:
            return 1.0
        
        # Check if target is substring of candidate
        if target_norm in candidate_norm:
            return 0.9
        
        # Check if candidate is substring of target
        if candidate_norm in target_norm:
            return 0.85
        
        # Calculate character overlap score
        target_chars = set(target_norm)
        candidate_chars = set(candidate_norm)
        
        if not target_chars or not candidate_chars:
            return 0.0
        
        intersection = len(target_chars.intersection(candidate_chars))
        union = len(target_chars.union(candidate_chars))
        
        jaccard_score = intersection / union if union > 0 else 0.0
        
        # Bonus for similar length
        length_diff = abs(len(target_norm) - len(candidate_norm))
        max_length = max(len(target_norm), len(candidate_norm))
        length_bonus = (max_length - length_diff) / max_length if max_length > 0 else 0.0
        
        return (jaccard_score * 0.7) + (length_bonus * 0.3)
    
    def find_best_matches(self, target_name: str, channels: List[dict], threshold: float = 0.5) -> List[Tuple[dict, float]]:
        """Find best matching channels using fuzzy matching"""
        matches = []
        
        for channel in channels:
            channel_name = channel.get('name', '')
            if not channel_name:
                continue
            
            score = self.calculate_fuzzy_score(target_name, channel_name)
            if score >= threshold:
                matches.append((channel, score))
        
        # Sort by score descending
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches
    
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
        
        all_channels = []
        
        # First, collect all channels for fuzzy matching
        for types in channel_types:
            channels = self._get_channels_by_type(app_token, types)
            all_channels.extend(channels)
            time.sleep(1)
        
        if not all_channels:
            print(f"❌ No channels found")
            return None
        
        # Try exact match first (both original and normalized)
        for channel in all_channels:
            channel_name = channel.get('name', '')
            # Check exact match with original clean name
            if channel_name == clean_name:
                channel_id = channel.get('id')
                print(f"✅ Exact match found - Channel: #{channel_name} - ID: {channel_id}")
                return channel_id
            # Check normalized match (handles #channel-name vs channel_name etc)
            if self.normalize_channel_name(channel_name) == self.normalize_channel_name(clean_name):
                channel_id = channel.get('id')
                print(f"✅ Normalized exact match found - Channel: #{channel_name} - ID: {channel_id}")
                return channel_id
        
        # Use fuzzy matching if no exact match
        matches = self.find_best_matches(clean_name, all_channels, threshold=0.5)
        
        if matches:
            best_match, score = matches[0]
            channel_id = best_match.get('id')
            channel_name = best_match.get('name')
            print(f"✅ Fuzzy match found - Channel: #{channel_name} (Score: {score:.2f}) - ID: {channel_id}")
            
            # Show additional matches if available
            if len(matches) > 1:
                print("Other possible matches:")
                for channel, match_score in matches[1:4]:  # Show top 3 alternatives
                    alt_name = channel.get('name')
                    print(f"  - #{alt_name} (Score: {match_score:.2f})")
            
            return channel_id
        
        print(f"❌ No matching channel found for '{clean_name}'")
        return None
    
    def _get_channels_by_type(self, token: str, channel_types: str) -> List[dict]:
        """Get all channels of specified types"""
        channels = []
        cursor = ""
        
        while True:
            endpoint = f"conversations.list?types={channel_types}&limit=1000"
            if cursor:
                endpoint += f"&cursor={cursor}"
            
            result = self.make_slack_request(endpoint, token)
            if not result:
                break
            
            page_channels = result.get('channels', [])
            channels.extend(page_channels)
            
            cursor = result.get('response_metadata', {}).get('next_cursor')
            if not cursor:
                break
                
            time.sleep(1)
        
        return channels

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
'''

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
            content=FIND_CHANNEL_SCRIPT
        )
    ],
    args=[
        Arg(name="channel_name", type="str", description="Channel name to search for (with or without # prefix)", required=True),
    ],
    secrets=["slack_app_token"]
)

# Register the tool
tool_registry.register("slack", find_channel_tool)