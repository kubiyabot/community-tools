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
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

def execute_slack_action(token, action, **kwargs):
    client = WebClient(token=token)
    try:
        method = getattr(client, action)
        response = method(**kwargs)
        return {{"success": True, "result": response.data}}
    except SlackApiError as e:
        return {{"success": False, "error": str(e)}}

if __name__ == "__main__":
    token = os.environ.get("SLACK_BOT_TOKEN")
    if not token:
        print(json.dumps({{"success": False, "error": "SLACK_BOT_TOKEN is not set"}}))
        sys.exit(1)

    arg_names = {arg_names_json}
    args = {{}}
    for arg in arg_names:
        if arg in os.environ:
            args[arg] = os.environ[arg]
    
    result = execute_slack_action(token, "{action}", **args)
    print(json.dumps(result))
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