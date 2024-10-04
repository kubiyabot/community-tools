from kubiya_sdk.tools.models import Tool, Arg, FileSpec
import json

KUBIYA_ICON_URL = "https://media.licdn.com/dms/image/D560BAQFaDnQXq7Dtbg/company-logo_200_200/0/1687904106468/kubiya_logo?e=2147483647&v=beta&t=7XFSmE0tW60OylcOGoSMW1oMDUqdH8p8gwCfXLGQnj4"

class KubiyaTool(Tool):
    def __init__(self, name, description, action, args, long_running=False, mermaid_diagram=None):
        env = ["KUBIYA_API_KEY", "KUBIYA_USER_EMAIL", "KUBIYA_USER_ORG", "KUBIYA_AGENT_UUID"]
        
        arg_names_json = json.dumps([arg.name for arg in args])
        
        script_content = f"""
import os
import sys
import requests
from datetime import datetime
import uuid

def execute_kubiya_action(action, **kwargs):
    if action == "schedule_task":
        return schedule_task(**kwargs)
    elif action == "create_webhook":
        return create_webhook(**kwargs)
    else:
        raise ValueError(f"Unsupported action: {action}")

def schedule_task(**kwargs):
    # Implement task scheduling logic here
    pass

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
        print(f"Error: {{e}}")
        sys.exit(1)
"""
        super().__init__(
            name=name,
            description=description,
            icon_url=KUBIYA_ICON_URL,
            type="docker",
            image="python:3.11",
            content="python /tmp/script.py",
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