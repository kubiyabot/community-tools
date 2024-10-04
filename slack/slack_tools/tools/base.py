from kubiya_sdk.tools.models import Tool, Arg, FileSpec
import json
import logging
from slack_sdk.web import SlackResponse

SLACK_ICON_URL = "https://a.slack-edge.com/80588/marketing/img/icons/icon_slack_hash_colored.png"

class SlackResponseEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, SlackResponse):
            return obj.data
        return super().default(obj)

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
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from slack_sdk.web import SlackResponse

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class SlackResponseEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, SlackResponse):
            return obj.data
        return super().default(obj)

def find_channel_id(client, channel_name):
    try:
        for result in client.conversations_list():
            for channel in result["channels"]:
                if channel["name"] == channel_name:
                    return channel["id"]
        return None
    except SlackApiError as e:
        logging.error(f"Error listing conversations: {{e}}")
        return None

def send_slack_message(client, channel, text):
    try:
        if channel.startswith('#'):
            channel_id = find_channel_id(client, channel[1:])
            if not channel_id:
                return {{"success": False, "error": f"Channel '{{channel}}' not found"}}
        else:
            channel_id = channel

        response = client.chat_postMessage(channel=channel_id, text=text)
        return {{"success": True, "result": response}}
    except SlackApiError as e:
        logging.error(f"Error sending message: {{e}}")
        return {{"success": False, "error": str(e), "response": e.response}}

def execute_slack_action(token, action, **kwargs):
    client = WebClient(token=token)
    logging.info(f"Executing Slack action: {{action}}")
    logging.info(f"Action parameters: {{kwargs}}")

    try:
        if action == "chat_postMessage":
            return send_slack_message(client, kwargs['channel'], kwargs['text'])
        else:
            method = getattr(client, action)
            response = method(**kwargs)
            return {{"success": True, "result": response}}
    except SlackApiError as e:
        logging.error(f"SlackApiError: {{e}}")
        return {{"success": False, "error": str(e), "response": e.response}}
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
            content="pip install slack_sdk && python /tmp/script.py",
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