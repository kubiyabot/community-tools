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
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def send_slack_message(client, channel_name, text):
    print("Starting to send Slack message...")
    try:
        # Remove '#' if present in channel name
        channel_name = channel_name.lstrip('#')
        print(f"Preparing to send message to channel: {{channel_name}}")

        # Prepare the message with disclaimer
        kubiya_user_email = os.environ.get("KUBIYA_USER_EMAIL", "Unknown User")
        full_message = f"{{text}}\\n\\n_This message was sent through the Kubiya platform by {{kubiya_user_email}}._"
        print("Message prepared with disclaimer")

        # Try to send the message
        print("Attempting to send message...")
        response = client.chat_postMessage(channel=channel_name, text=full_message)
        print(f"Message sent successfully to {{channel_name}}")
        return {{"success": True, "result": response.data, "thread_ts": response['ts']}}

    except SlackApiError as e:
        error_message = str(e)
        print(f"Error sending message: {{error_message}}")

        if "channel_not_found" in error_message:
            print("Channel not found. Attempting to look up channel...")
            # If channel not found, try to find it
            try:
                print("Listing conversations...")
                channels = client.conversations_list()
                for channel in channels["channels"]:
                    if channel["name"] == channel_name:
                        channel_id = channel["id"]
                        print(f"Channel found. ID: {{channel_id}}")
                        print("Sending message to found channel...")
                        response = client.chat_postMessage(channel=channel_id, text=full_message)
                        print(f"Message sent successfully to {{channel_name}} after lookup")
                        return {{"success": True, "result": response.data, "thread_ts": response['ts']}}
                print("Channel not found in the list")
            except SlackApiError as lookup_error:
                print(f"Error during channel lookup: {{lookup_error}}")

        return {{"success": False, "error": error_message}}

def execute_slack_action(token, action, **kwargs):
    client = WebClient(token=token)
    print(f"Executing Slack action: {{action}}")
    print(f"Action parameters: {{kwargs}}")

    try:
        if action == "chat_postMessage":
            result = send_slack_message(client, kwargs['channel_name'], kwargs['text'])
        else:
            print(f"Executing action: {{action}}")
            method = getattr(client, action)
            response = method(**kwargs)
            result = {{"success": True, "result": response.data}}
            if 'ts' in response.data:
                result['thread_ts'] = response.data['ts']
        
        print(f"Action completed. Result: {{result}}")
        return result
    except Exception as e:
        print(f"Unexpected error: {{e}}")
        return {{"success": False, "error": str(e)}}

if __name__ == "__main__":
    token = os.environ.get("SLACK_API_TOKEN")
    if not token:
        print("SLACK_API_TOKEN is not set")
        print(json.dumps({{"success": False, "error": "SLACK_API_TOKEN is not set"}}))
        sys.exit(1)

    print("Starting Slack action execution...")
    arg_names = {arg_names_json}
    args = {{}}
    for arg in arg_names:
        if arg in os.environ:
            args[arg] = os.environ[arg]
    
    result = execute_slack_action(token, "{action}", **args)
    print("Slack action execution completed")
    print(json.dumps(result))
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