from kubiya_sdk.tools.models import Tool, Arg, FileSpec
import json

SLACK_ICON_URL = "https://a.slack-edge.com/80588/marketing/img/icons/icon_slack_hash_colored.png"

class SlackTool(Tool):
    def __init__(self, name, description, action, args, long_running=False, mermaid_diagram=None):
        env = ["KUBIYA_USER_EMAIL"]
        secrets = ["SLACK_API_TOKEN"]
        
        arg_names_json = json.dumps([arg.name for arg in args])
        
        script_content = f"""
import os
import sys
import json
import logging
import re
import subprocess
from datetime import datetime

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# Install required packages
install('slack_sdk')
install('fuzzywuzzy')
install('python-Levenshtein')

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from slack_sdk.web import SlackResponse
from fuzzywuzzy import process

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class SlackResponseEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, SlackResponse):
            return obj.data
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        return super().default(obj)

def find_channel_id(client, channel_input, fuzzy_match=True):
    channel_input = channel_input.lstrip('#')
    
    # Check if it's already a channel ID
    if re.match(r'^[C][A-Z0-9]{{8,}}$', channel_input):
        return channel_input

    try:
        channels = []
        for result in client.conversations_list():
            channels.extend(result["channels"])
        
        # Exact match
        for channel in channels:
            if channel["name"] == channel_input:
                return channel["id"]
        
        if fuzzy_match:
            # Fuzzy match
            channel_names = [channel["name"] for channel in channels]
            best_matches = process.extract(channel_input, channel_names, limit=5)
            
            if best_matches and best_matches[0][1] >= 80:  # 80% similarity threshold
                matched_channel = next(channel for channel in channels if channel["name"] == best_matches[0][0])
                return matched_channel["id"]
            else:
                options = [{{
                    "name": match[0],
                    "score": match[1],
                    "id": next(channel["id"] for channel in channels if channel["name"] == match[0])
                }} for match in best_matches]
                return {{"error": "No high confidence match found", "options": options}}
        
        return None
    except SlackApiError as e:
        logging.error(f"Error listing conversations: {{e}}")
        return None

def send_slack_message(client, channel, text):
    try:
        channel_id_result = find_channel_id(client, channel, fuzzy_match=True)
        
        if isinstance(channel_id_result, dict) and "error" in channel_id_result:
            return channel_id_result
        
        if not channel_id_result:
            return {{"success": False, "error": f"Channel '{{channel}}' not found"}}

        response = client.chat_postMessage(channel=channel_id_result, text=text)
        return {{"success": True, "result": response.data}}
    except SlackApiError as e:
        logging.error(f"Error sending message: {{e}}")
        return {{"success": False, "error": str(e), "response": e.response.data if e.response else None}}

def execute_slack_action(token, action, **kwargs):
    client = WebClient(token=token)
    logging.info(f"Executing Slack action: {{action}}")
    logging.info(f"Action parameters: {{kwargs}}")

    try:
        if action == "chat_postMessage":
            result = send_slack_message(client, kwargs['channel'], kwargs['text'])
        else:
            method = getattr(client, action)
            response = method(**kwargs)
            result = {{"success": True, "result": response.data}}
        
        return result
    except SlackApiError as e:
        logging.error(f"SlackApiError: {{e}}")
        return {{"success": False, "error": str(e), "response": e.response.data if e.response else None}}
    except Exception as e:
        logging.error(f"Unexpected error: {{e}}")
        return {{"success": False, "error": str(e)}}

if __name__ == "__main__":
    token = os.environ.get("SLACK_API_TOKEN")
    if not token:
        logging.error("SLACK_API_TOKEN is not set")
        print(json.dumps({{"success": False, "error": "SLACK_API_TOKEN is not set"}}))
        sys.exit(1)

    arg_names = {arg_names_json}
    args = {{}}
    for arg in arg_names:
        if arg in os.environ:
            args[arg] = os.environ[arg]
    
    result = execute_slack_action(token, "{action}", **args)
    print(json.dumps(result, cls=SlackResponseEncoder))
"""
        super().__init__(
            name=name,
            description=description,
            icon_url=SLACK_ICON_URL,
            type="docker",
            image="python:3.11-slim",
            content="python /tmp/script.py",
            args=args,
            env=env,
            secrets=secrets,
            long_running=long_running,
            mermaid=mermaid_diagram,
            with_files=[
                FileSpec(
                    destination="/tmp/script.py",
                    content=script_content,
                )
            ],
        )