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

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from slack_sdk.web import SlackResponse

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

def find_channel_or_user(client, input_value):
    input_value = input_value.lstrip('#@')
    
    # Check if it's already a channel or user ID
    if re.match(r'^[CU][A-Z0-9]{{8,}}$', input_value):
        return input_value

    try:
        # Try to find channel
        response = client.conversations_list(types="public_channel,private_channel")
        for channel in response["channels"]:
            if channel["name"] == input_value:
                return channel["id"]
        
        # Try to find user
        response = client.users_list()
        for user in response["members"]:
            if user["name"] == input_value or user["real_name"] == input_value:
                return user["id"]
        
        return None
    except SlackApiError as e:
        logging.error(f"Error finding channel or user: {{e}}")
        return None

def get_styled_blocks(text, style):
    if style == "simple" or not style:
        return [{{"type": "section", "text": {{"type": "mrkdwn", "text": text}}}}]
    
    color_map = {{
        "info": "#3498db",
        "warning": "#f39c12",
        "success": "#2ecc71",
        "error": "#e74c3c"
    }}
    
    if style in color_map:
        return [
            {{
                "type": "header",
                "text": {{
                    "type": "plain_text",
                    "text": style.capitalize(),
                    "emoji": True
                }}
            }},
            {{
                "type": "divider"
            }},
            {{
                "type": "section",
                "text": {{"type": "mrkdwn", "text": text}}
            }},
            {{
                "type": "context",
                "elements": [
                    {{
                        "type": "mrkdwn",
                        "text": f"*{{style.capitalize()}}*"
                    }}
                ]
            }}
        ]
    
    return [{{"type": "section", "text": {{"type": "mrkdwn", "text": text}}}}]

def send_slack_message(client, channel, text, style=None):
    try:
        # If channel starts with '#', remove it and try to find the channel
        if channel.startswith('#'):
            channel_name = channel[1:]
            try:
                # List all channels and find the matching one
                response = client.conversations_list(types="public_channel,private_channel")
                for ch in response["channels"]:
                    if ch["name"] == channel_name:
                        channel_id = ch["id"]
                        break
                else:
                    return {{"success": False, "error": f"Channel '{{channel}}' not found"}}
            except SlackApiError as e:
                logging.error(f"Error listing channels: {{e}}")
                return {{"success": False, "error": f"Failed to list channels: {{str(e)}}"}}
        elif channel.startswith('C'):
            channel_id = channel
        else:
            # Assume it's a user ID
            channel_id = channel

        blocks = get_styled_blocks(text, style)
        
        kubiya_user_email = os.environ.get("KUBIYA_USER_EMAIL")
        if kubiya_user_email:
            disclaimer = f"This message was sent by <@{{kubiya_user_email}}> using the Kubiya platform as part of a request/workflow."
            blocks.append({{"type": "context", "elements": [{{"type": "mrkdwn", "text": disclaimer}}]}})

        # Check message length and truncate if necessary
        max_text_length = 3000
        if len(text) > max_text_length:
            text = text[:max_text_length-3] + "..."
            for block in blocks:
                if block["type"] == "section" and "text" in block["text"]:
                    block["text"]["text"] = text

        response = client.chat_postMessage(channel=channel_id, text=text, blocks=blocks)
        return {{"success": True, "result": response.data}}

    except SlackApiError as e:
        error_message = str(e)
        if "invalid_blocks" in error_message:
            # Fallback to simple text message if blocks are invalid
            try:
                response = client.chat_postMessage(channel=channel_id, text=text)
                return {{"success": True, "result": response.data, "warning": "Fell back to simple text message due to invalid blocks"}}
            except SlackApiError as simple_e:
                return {{"success": False, "error": f"Failed to send even a simple message: {{simple_e}}"}}
        elif "rate_limited" in error_message:
            retry_after = e.response.headers.get("Retry-After", 1)
            return {{"success": False, "error": f"Rate limited. Retry after {{retry_after}} seconds", "retry_after": int(retry_after)}}
        else:
            logging.error(f"Error sending message: {{e}}")
            return {{"success": False, "error": error_message, "response": e.response.data if e.response else None}}

def execute_slack_action(token, action, **kwargs):
    client = WebClient(token=token)
    logging.info(f"Executing Slack action: {{action}}")
    logging.info(f"Action parameters: {{kwargs}}")

    try:
        if action == "chat_postMessage":
            result = send_slack_message(client, kwargs['channel'], kwargs['text'], kwargs.get('style'))
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