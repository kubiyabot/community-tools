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
from fuzzywuzzy import fuzz

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_block_kit_message(text, kubiya_user_email, kubiya_agent_profile, kubiya_agent_uuid):
    return [
        {{
            "type": "section",
            "text": {{"type": "mrkdwn", "text": text}}
        }},
        {{
            "type": "divider"
        }},
        {{
            "type": "context",
            "elements": [
                {{
                    "type": "mrkdwn",
                    "text": f":robot_face: This message was sent on behalf of <@{{kubiya_user_email}}> using the Kubiya AI platform"
                }}
            ]
        }},
        {{
            "type": "section",
            "text": {{
                "type": "mrkdwn",
                "text": f"*Kubiya Teammate:* {{kubiya_agent_profile}}\\n_This AI teammate assisted in generating and sending this message._"
            }}
        }},
        {{
            "type": "section",
            "text": {{
                "type": "mrkdwn",
                "text": "_Note: Conversing directly with this teammate may require special permissions._"
            }}
        }},
        {{
            "type": "actions",
            "elements": [
                {{
                    "type": "button",
                    "text": {{"type": "plain_text", "text": "View Teammate Settings", "emoji": True}},
                    "url": f"https://app.kubiya.ai/teammates/overview/{{kubiya_agent_uuid}}",
                    "action_id": "view_teammate_settings"
                }}
            ]
        }}
    ]

def find_channel(client, channel_input):
    channel_input = channel_input.lstrip('#')
    
    # Check if it's already a valid channel ID
    try:
        result = client.conversations_info(channel=channel_input)
        return channel_input
    except SlackApiError:
        pass

    # Search for the channel
    try:
        for response in client.conversations_list(types="public_channel,private_channel"):
            for channel in response["channels"]:
                if channel["name"] == channel_input:
                    return channel["id"]
                elif fuzz.ratio(channel["name"], channel_input) > 80:
                    logger.info(f"Found close match: {{channel['name']}} (ID: {{channel['id']}})")
                    return channel["id"]
        
        logger.error(f"Channel not found: {{channel_input}}")
        return None
    except SlackApiError as e:
        logger.error(f"Error listing channels: {{e}}")
        return None

def send_slack_message(client, channel, text):
    logger.info(f"Starting to send Slack message to: {{channel}}")
    
    channel_id = find_channel(client, channel)
    if not channel_id:
        return {{"success": False, "error": f"Channel not found: {{channel}}"}}

    try:
        kubiya_user_email = os.environ.get("KUBIYA_USER_EMAIL", "Unknown User")
        kubiya_agent_profile = os.environ.get("KUBIYA_AGENT_PROFILE", "Unknown Agent")
        kubiya_agent_uuid = os.environ.get("KUBIYA_AGENT_UUID", "unknown")
        
        blocks = create_block_kit_message(text, kubiya_user_email, kubiya_agent_profile, kubiya_agent_uuid)
        
        fallback_text = (
            f"{{text}}\\n\\n_This message was sent on behalf of <@{{kubiya_user_email}}> "
            f"using the Kubiya platform (Teammate: {{kubiya_agent_profile}})_"
        )

        logger.info("Attempting to send Block Kit message...")
        try:
            response = client.chat_postMessage(channel=channel_id, blocks=blocks, text=fallback_text)
            logger.info(f"Block Kit message sent successfully to {{channel_id}}")
        except SlackApiError as block_error:
            logger.warning(f"Failed to send Block Kit message: {{block_error}}. Falling back to regular message.")
            response = client.chat_postMessage(channel=channel_id, text=fallback_text)
            logger.info(f"Regular message sent successfully to {{channel_id}}")

        return {{"success": True, "result": response.data, "thread_ts": response['ts']}}

    except SlackApiError as e:
        error_message = str(e)
        logger.error(f"Error sending message: {{error_message}}")
        return {{"success": False, "error": error_message}}

def execute_slack_action(token, action, **kwargs):
    client = WebClient(token=token)
    logger.info(f"Executing Slack action: {{action}}")
    logger.info(f"Action parameters: {{kwargs}}")

    try:
        if action == "chat_postMessage":
            result = send_slack_message(client, kwargs['channel'], kwargs['text'])
        else:
            logger.info(f"Executing action: {{action}}")
            method = getattr(client, action)
            response = method(**kwargs)
            result = {{"success": True, "result": response.data}}
            if 'ts' in response.data:
                result['thread_ts'] = response.data['ts']
        
        logger.info(f"Action completed. Result: {{result}}")
        return result
    except Exception as e:
        logger.error(f"Unexpected error: {{e}}")
        return {{"success": False, "error": str(e)}}

if __name__ == "__main__":
    token = os.environ.get("SLACK_API_TOKEN")
    if not token:
        logger.error("SLACK_API_TOKEN is not set")
        print(json.dumps({{"success": False, "error": "SLACK_API_TOKEN is not set"}}))
        sys.exit(1)

    logger.info("Starting Slack action execution...")
    arg_names = {arg_names_json}
    args = {{}}
    for arg in arg_names:
        if arg in os.environ:
            args[arg] = os.environ[arg]
    
    result = execute_slack_action(token, "{action}", **args)
    logger.info("Slack action execution completed")
    print(json.dumps(result))
"""
        super().__init__(
            name=name,
            description=description,
            icon_url=SLACK_ICON_URL,
            type="docker",
            image="python:3.11-slim",
            content="pip install slack-sdk fuzzywuzzy python-Levenshtein && python /tmp/script.py",
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
