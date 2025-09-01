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
        
        # Check if either is empty
        if not target_norm or not candidate_norm:
            return 0.0
            
        # Early exit for very different lengths (likely false positive)
        length_ratio = min(len(target_norm), len(candidate_norm)) / max(len(target_norm), len(candidate_norm))
        if length_ratio < 0.2:  # Reduced from 0.3 to allow more flexibility
            return 0.0
        
        # Substring matching with better scoring
        if target_norm in candidate_norm:
            # Perfect substring match gets high score, but not perfect
            # Longer matches in shorter strings get higher scores
            score = 0.85 + (len(target_norm) / len(candidate_norm)) * 0.1
            return min(score, 0.95)  # Cap at 0.95 to keep below exact match
        
        if candidate_norm in target_norm:
            # Reverse substring match, slightly lower score
            score = 0.8 + (len(candidate_norm) / len(target_norm)) * 0.1
            return min(score, 0.9)
        
        # Enhanced token-based matching for complex names
        token_score = self._calculate_enhanced_token_score(target, candidate)
        
        # Calculate sequential character matching (better than just set intersection)
        lcs_score = self._longest_common_subsequence_ratio(target_norm, candidate_norm)
        
        # Calculate character overlap score as fallback
        target_chars = set(target_norm)
        candidate_chars = set(candidate_norm)
        intersection = len(target_chars.intersection(candidate_chars))
        union = len(target_chars.union(candidate_chars))
        jaccard_score = intersection / union if union > 0 else 0.0
        
        # Position-aware matching: check if words/tokens align
        position_score = self._calculate_position_score(target_norm, candidate_norm)
        
        # Length similarity bonus
        length_similarity = 1 - (abs(len(target_norm) - len(candidate_norm)) / max(len(target_norm), len(candidate_norm)))
        
        # Combine scores with enhanced token matching
        final_score = (
            token_score * 0.35 +        # Enhanced token matching (higher weight)
            lcs_score * 0.3 +           # Sequential character matching  
            position_score * 0.2 +      # Word/token position alignment
            jaccard_score * 0.1 +       # Character overlap
            length_similarity * 0.05    # Length similarity (reduced weight)
        )
        
        # More flexible threshold for complex channel names
        # Lower threshold but with additional validation
        if final_score < 0.65:
            return 0.0
        
        # For high-confidence matches on token alignment, boost the score
        if token_score > 0.8 and final_score > 0.7:
            final_score = min(final_score * 1.1, 0.95)  # 10% boost, capped
            
        return final_score
    
    def _longest_common_subsequence_ratio(self, s1: str, s2: str) -> float:
        """Calculate ratio of longest common subsequence to average string length"""
        def lcs_length(x, y):
            m, n = len(x), len(y)
            if m == 0 or n == 0:
                return 0
            
            # Create DP table
            dp = [[0] * (n + 1) for _ in range(m + 1)]
            
            for i in range(1, m + 1):
                for j in range(1, n + 1):
                    if x[i-1] == y[j-1]:
                        dp[i][j] = dp[i-1][j-1] + 1
                    else:
                        dp[i][j] = max(dp[i-1][j], dp[i][j-1])
            
            return dp[m][n]
        
        lcs_len = lcs_length(s1, s2)
        avg_len = (len(s1) + len(s2)) / 2
        return lcs_len / avg_len if avg_len > 0 else 0.0
    
    def _calculate_position_score(self, target: str, candidate: str) -> float:
        """Calculate score based on word/token position alignment"""
        # Split on common separators and compare token positions
        target_tokens = re.split(r'[_\-\s]+', target.lower())
        candidate_tokens = re.split(r'[_\-\s]+', candidate.lower())
        
        if not target_tokens or not candidate_tokens:
            return 0.0
        
        # Remove empty tokens
        target_tokens = [t for t in target_tokens if t]
        candidate_tokens = [t for t in candidate_tokens if t]
        
        if not target_tokens or not candidate_tokens:
            return 0.0
        
        # Calculate how many target tokens appear in candidate tokens
        matches = 0
        for target_token in target_tokens:
            for candidate_token in candidate_tokens:
                # Exact token match
                if target_token == candidate_token:
                    matches += 1
                    break
                # Substring match within token
                elif target_token in candidate_token or candidate_token in target_token:
                    matches += 0.7
                    break
        
        return matches / len(target_tokens)
    
    def _calculate_enhanced_token_score(self, target: str, candidate: str) -> float:
        """Enhanced token-based scoring for complex channel names"""
        # Extract tokens from both strings using multiple separators
        target_tokens = re.split(r'[_\-\s.]+', target.lower().strip('#'))
        candidate_tokens = re.split(r'[_\-\s.]+', candidate.lower().strip('#'))
        
        # Remove empty tokens
        target_tokens = [t for t in target_tokens if t and len(t) > 0]
        candidate_tokens = [t for t in candidate_tokens if t and len(t) > 0]
        
        if not target_tokens or not candidate_tokens:
            return 0.0
        
        # Calculate exact token matches
        exact_matches = 0
        partial_matches = 0
        
        for target_token in target_tokens:
            best_match_score = 0
            for candidate_token in candidate_tokens:
                if target_token == candidate_token:
                    exact_matches += 1
                    best_match_score = 1.0
                    break
                elif target_token in candidate_token or candidate_token in target_token:
                    # Partial match - score based on length ratio
                    if len(target_token) >= 3 and len(candidate_token) >= 3:  # Only for meaningful tokens
                        overlap_ratio = min(len(target_token), len(candidate_token)) / max(len(target_token), len(candidate_token))
                        best_match_score = max(best_match_score, overlap_ratio * 0.8)
                elif self._tokens_similar(target_token, candidate_token):
                    # Similar tokens (edit distance)
                    best_match_score = max(best_match_score, 0.6)
            
            if best_match_score > 0.5:
                partial_matches += best_match_score
        
        # Calculate score based on match ratio
        total_score = (exact_matches + partial_matches) / len(target_tokens)
        
        # Bonus for high coverage of candidate tokens (bidirectional matching)
        reverse_matches = 0
        for candidate_token in candidate_tokens:
            for target_token in target_tokens:
                if candidate_token == target_token or candidate_token in target_token or target_token in candidate_token:
                    reverse_matches += 1
                    break
        
        coverage_score = reverse_matches / len(candidate_tokens) if candidate_tokens else 0
        
        # Combine forward and reverse matching
        final_score = (total_score * 0.7) + (coverage_score * 0.3)
        
        return min(final_score, 1.0)
    
    def _tokens_similar(self, token1: str, token2: str) -> bool:
        """Check if two tokens are similar using simple edit distance"""
        if len(token1) < 3 or len(token2) < 3:
            return False
        
        # Simple edit distance check
        max_len = max(len(token1), len(token2))
        min_len = min(len(token1), len(token2))
        
        if max_len - min_len > 2:  # Too different in length
            return False
        
        differences = 0
        for i in range(min_len):
            if token1[i] != token2[i]:
                differences += 1
                if differences > 1:  # Allow only 1 character difference
                    return False
        
        return differences <= 1
    
    def find_best_matches(self, target_name: str, channels: List[dict], threshold: float = 0.5, max_matches: int = 5) -> List[Tuple[dict, float]]:
        """Find best matching channels using fuzzy matching"""
        matches = []
        
        for channel in channels:
            channel_name = channel.get('name', '')
            if not channel_name:
                continue
            
            score = self.calculate_fuzzy_score(target_name, channel_name)
            if score >= threshold:
                matches.append((channel, score))
        
        # Sort by score descending and limit results for large channel sets
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches[:max_matches]
    
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
        
        # Use fuzzy matching if no exact match - balanced threshold for complex channel names
        matches = self.find_best_matches(clean_name, all_channels, threshold=0.7, max_matches=3)
        
        if matches:
            best_match, score = matches[0]
            
            # Adjusted safety check for complex channel names
            # Allow lower confidence for complex names but still prevent false positives
            if score < 0.75:
                print(f"❌ Best match '{best_match.get('name')}' has low confidence (Score: {score:.2f})")
                print("Try a more specific channel name to improve matching accuracy")
                return None
            
            channel_id = best_match.get('id')
            channel_name = best_match.get('name')
            print(f"✅ Fuzzy match found - Channel: #{channel_name} (Score: {score:.2f}) - ID: {channel_id}")
            
            # Show additional matches if available
            if len(matches) > 1:
                print("Other possible matches:")
                for channel, match_score in matches[1:]:  # Show remaining alternatives
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