from kubiya_sdk.tools.models import Tool, Arg, FileSpec
import json

KUBIYA_ICON_URL = "https://media.licdn.com/dms/image/v2/D560BAQG9BrF3G3A3Aw/company-logo_200_200/company-logo_200_200/0/1726534282425/kubiya_logo?e=2147483647&v=beta&t=2BT_nUHPJVNqbU2JjeU5XEWF6y2kn78xr-WZQcYVq5s"

class KubiyaTool(Tool):
    def __init__(self, name, description, action, args, long_running=False, mermaid_diagram=None):
        env = ["KUBIYA_API_KEY", "KUBIYA_USER_EMAIL", "KUBIYA_USER_ORG", "KUBIYA_AGENT_UUID", "SLACK_CHANNEL_ID", "KUBIYA_AGENT_PROFILE"]
        
        arg_names_json = json.dumps([arg.name for arg in args])
        
        script_content = f"""
import os
import sys
import requests

from datetime import datetime, timedelta, timezone
from pytimeparse.timeparse import timeparse
import json

def execute_kubiya_action(action, **kwargs):
    if action == "schedule_task":
        return schedule_task(**kwargs)
    elif action == "create_webhook":
        return create_webhook(**kwargs)
    else:
        raise ValueError(f"Unsupported action: {{action}}")

def parse_duration(duration):
    seconds = timeparse(duration)
    if seconds is None:
        raise ValueError("Invalid duration format. Please use a valid format (e.g., 5h for 5 hours, 30m for 30 minutes).")
    return timedelta(seconds=seconds)

def calculate_schedule_time(duration):
    now = datetime.now(timezone.utc)
    return now + parse_duration(duration)

def schedule_task(execution_delay, **kwargs):
    required_vars = [
        "KUBIYA_API_KEY", "SLACK_CHANNEL_ID", "KUBIYA_USER_EMAIL", "KUBIYA_USER_ORG", "KUBIYA_AGENT_PROFILE"
    ]
    for var in required_vars:
        if var not in os.environ:
            raise ValueError(f"{{var}} is not set. Please set the {{var}} environment variable.")

    schedule_time = calculate_schedule_time(execution_delay)
    
    payload = {{
        "scheduled_time": schedule_time.isoformat(),
        "channel_id": os.environ["SLACK_CHANNEL_ID"],
        "user_email": os.environ["KUBIYA_USER_EMAIL"],
        "organization_name": os.environ["KUBIYA_USER_ORG"],
        "task_description": "say hello",
        "agent": os.environ["KUBIYA_AGENT_PROFILE"]
    }}
    
    response = requests.post(
        'https://api.kubiya.ai/api/v1/scheduled_tasks',
        headers={{
            'Authorization': f'UserKey {{os.environ["KUBIYA_API_KEY"]}}',
            'Content-Type': 'application/json'
        }},
        json=payload
    )
    
    if response.status_code < 300:
        return {{"message": "Task scheduled successfully", "response": response.text}}
    else:
        raise ValueError(f"Error: {{response.status_code}} - {{response.text}}")

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
            content="pip install requests pytimeparse && python /tmp/script.py",
            args=args,
            env=env,
            long_running=long_running,
            mermaid=mermaid_diagram,
            with_files=[
                FileSpec(
                    destination="/tmp/script.py",
                    content=script_content,
                )
            ],
        )
