from kubiya_sdk.tools.models import Tool, Arg, FileSpec
import json

KUBIYA_ICON_URL = "https://media.licdn.com/dms/image/v2/D560BAQG9BrF3G3A3Aw/company-logo_200_200/company-logo_200_200/0/1726534282425/kubiya_logo?e=2147483647&v=beta&t=2BT_nUHPJVNqbU2JjeU5XEWF6y2kn78xr-WZQcYVq5s"

class KubiyaTool(Tool):
    def __init__(self, name, description, action, args, long_running=False, mermaid_diagram=None):
        env = ["KUBIYA_USER_EMAIL", "KUBIYA_USER_ORG", "KUBIYA_AGENT_UUID", "SLACK_CHANNEL_ID", "KUBIYA_AGENT_PROFILE"]
        secrets = ["KUBIYA_API_KEY", "SLACK_API_TOKEN"]
        
        arg_names_json = json.dumps([arg.name for arg in args])
        
        script_content = f"""
import os
import sys
import requests
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from fuzzywuzzy import process

from datetime import datetime, timedelta, timezone
from pytimeparse.timeparse import timeparse
import json

def execute_kubiya_action(action, **kwargs):
    if action == "schedule_task":
        return schedule_task(**kwargs)
    elif action == "create_webhook":
        return create_webhook(**kwargs)
    else:
        raise ValueError(f"Unsupported action: {{{{action}}}}")

def parse_duration(duration):
    seconds = timeparse(duration)
    if seconds is None:
        raise ValueError("Invalid duration format. Please use a valid format (e.g., 5h for 5 hours, 30m for 30 minutes).")
    return timedelta(seconds=seconds)

def calculate_schedule_time(duration):
    now = datetime.now(timezone.utc)
    return now + parse_duration(duration)

def find_slack_destination(client, name):
    channels = []
    users = []
    try:
        # Get all channels (public and private)
        for response in client.conversations_list(types="public_channel,private_channel"):
            channels.extend([(c["id"], c["name"]) for c in response["channels"]])
        
        # Get all users
        for response in client.users_list():
            users.extend([(u["id"], u["name"]) for u in response["members"]])
    except SlackApiError as e:
        print(f"Error fetching Slack data: {{{{e}}}}")
    
    all_destinations = channels + users
    matches = process.extract(name, [d[1] for d in all_destinations], limit=5)
    
    if matches and matches[0][1] > 80:  # If there's a good match (> 80% similarity)
        best_match = matches[0][0]
        for dest_id, dest_name in all_destinations:
            if dest_name == best_match:
                return dest_id, "channel" if (dest_id, dest_name) in channels else "user"
    elif matches:  # If there are some matches, but not very good ones
        options = [{{
            "id": next(d[0] for d in all_destinations if d[1] == m[0]),
            "name": m[0],
            "type": "channel" if next(d for d in all_destinations if d[1] == m[0]) in channels else "user",
            "score": m[1]
        }} for m in matches]
        raise ValueError(f"Multiple possible matches found. Please choose from: {{json.dumps(options, indent=2)}}")
    
    return None, None

def schedule_task(schedule_time, slack_destination=None, ai_instructions="", **kwargs):
    required_vars = [
        "KUBIYA_API_KEY", "KUBIYA_USER_EMAIL", "KUBIYA_USER_ORG", "KUBIYA_AGENT_PROFILE", "SLACK_API_TOKEN"
    ]
    for var in required_vars:
        if var not in os.environ:
            raise ValueError(f"{{var}} is not set. Please set the {{var}} environment variable.")

    execution_time = calculate_schedule_time(schedule_time)
    
    slack_client = WebClient(token=os.environ["SLACK_BOT_TOKEN"])
    
    if slack_destination:
        destination_id, destination_type = find_slack_destination(slack_client, slack_destination)
        if not destination_id:
            print(f"Warning: Could not find destination '{{{{slack_destination}}}}' in Slack.")
            fallback_channel = os.environ.get("SLACK_CHANNEL_ID")
            if fallback_channel:
                print(f"Falling back to default channel: {{{{fallback_channel}}}}")
                destination_id = fallback_channel
                destination_type = "channel"
            else:
                raise ValueError("No valid Slack destination found. Please provide a valid channel or user name, or set the SLACK_CHANNEL_ID environment variable.")
    else:
        destination_id = os.environ.get("SLACK_CHANNEL_ID")
        destination_type = "channel"
        if not destination_id:
            raise ValueError("No Slack destination specified and SLACK_CHANNEL_ID is not set. Please provide a valid channel or user name, or set the SLACK_CHANNEL_ID environment variable.")
    
    payload = {{
        "scheduled_time": execution_time.isoformat(),
        "channel_id": destination_id,
        "user_email": os.environ["KUBIYA_USER_EMAIL"],
        "organization_name": os.environ["KUBIYA_USER_ORG"],
        "task_description": ai_instructions,
        "agent": os.environ["KUBIYA_AGENT_PROFILE"],
        "destination_type": destination_type
    }}
    
    response = requests.post(
        'https://api.kubiya.ai/api/v1/scheduled_tasks',
        headers={{
            'Authorization': f'UserKey {{{{os.environ["KUBIYA_API_KEY"]}}}}',
            'Content-Type': 'application/json'
        }},
        json=payload
    )
    
    if response.status_code < 300:
        return {{
            "message": "Task scheduled successfully",
            "scheduled_time": execution_time.isoformat(),
            "destination": destination_id,
            "destination_type": destination_type,
            "ai_instructions": ai_instructions,
            "response": response.text
        }}
    else:
        raise ValueError(f"Error: {{{{response.status_code}}}} - {{{{response.text}}}}")

def create_webhook(**kwargs):
    # Implement webhook creation logic here
    pass

if __name__ == "__main__":
    arg_names = {arg_names_json}
    args = {{}}
    for arg in arg_names:
        if arg in os.environ:
            args[arg] = os.environ[arg]
    
    try:
        result = execute_kubiya_action("{action}", **args)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(json.dumps({{"error": str(e)}}))
        sys.exit(1)
"""
        super().__init__(
            name=name,
            description=description,
            icon_url=KUBIYA_ICON_URL,
            type="docker",
            image="python:3.11",
            on_build ="pip install requests pytimeparse slack_sdk fuzzywuzzy python-Levenshtein", 
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