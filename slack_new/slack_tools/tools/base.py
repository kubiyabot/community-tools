import os
import json
import requests
from typing import Dict, Any, Optional


class SlackBase:
    """Base class for Slack tools with token management"""
    
    def __init__(self):
        self.kubiya_token = None
        self.slack_app_token = None
    
    def get_kubiya_slack_token(self) -> Optional[str]:
        """Get basic Slack token from Kubiya integration API"""
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
    
    def get_slack_app_token(self) -> Optional[str]:
        """Get higher-tier Slack app token from Kubiya secrets API"""
        try:
            response = requests.get(
                "https://api.kubiya.ai/api/v1/secret/get_secret_value/slack_app_token",
                headers={"Authorization": f"Bearer {os.getenv('KUBIYA_API_TOKEN')}"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                # Handle different response formats
                token = data.get('value') or data.get('secret_value') or data.get('token')
                if token and token != 'null':
                    self.slack_app_token = token
                    return token
            
            print(f"Failed to get Slack app token: {response.status_code}")
            return None
            
        except Exception as e:
            print(f"Error getting Slack app token: {e}")
            return None
    
    def make_slack_request(self, endpoint: str, token: str, method: str = "GET", data: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """Make authenticated request to Slack API with rate limiting"""
        url = f"https://slack.com/api/{endpoint}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        try:
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=30)
            elif method == "POST":
                response = requests.post(url, headers=headers, json=data or {}, timeout=30)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    return result
                else:
                    print(f"Slack API error: {result.get('error')}")
                    return None
            elif response.status_code == 429:
                # Rate limited
                retry_after = int(response.headers.get('Retry-After', 1))
                print(f"Rate limited. Retry after {retry_after} seconds")
                return None
            else:
                print(f"HTTP error {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            print(f"Request error: {e}")
            return None