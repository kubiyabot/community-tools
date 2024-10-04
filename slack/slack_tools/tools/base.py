from kubiya_sdk.tools.models import Tool, Arg, FileSpec
import json

SLACK_ICON_URL = "https://a.slack-edge.com/80588/marketing/img/icons/icon_slack_hash_colored.png"

class SlackTool(Tool):
    def __init__(self, name, description, action, args, long_running=False, mermaid_diagram=None):
        env = ["KUBIYA_USER_EMAIL"]
        secrets = ["SLACK_API_TOKEN"]
        
        arg_names_json = json.dumps([arg.name for arg in args])
        
        script_content = f"""
import subprocess
import sys
import os
import json
import base64
from datetime import datetime

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# Install slack_sdk
install('slack_sdk')

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

def serialize_slack_response(obj, max_depth=10, max_items=100):
    def _serialize(o, depth):
        if depth > max_depth:
            return str(o)
        if isinstance(o, (str, int, float, bool, type(None))):
            return o
        if isinstance(o, (list, tuple)):
            return [_serialize(i, depth + 1) for i in o[:max_items]]
        if isinstance(o, dict):
            return {{k: _serialize(v, depth + 1) for k, v in list(o.items())[:max_items]}}
        return str(o)
    
    return _serialize(obj, 0)

def create_block_kit_message(template, **kwargs):
    print(f"Debug: Creating block kit message with template: {template}")
    print(f"Debug: kwargs: {kwargs}")
    try:
        formatted_template = [
            {k: v.format(**kwargs) if isinstance(v, str) else v for k, v in block.items()}
            for block in template
        ]
        blocks = json.dumps(formatted_template)
        text = f"{kwargs.get('title', '')}\n\n{kwargs.get('message', '')}"
        return {'blocks': blocks, 'text': text}
    except KeyError as e:
        print(f"Error: Missing key in kwargs: {e}")
        raise
    except Exception as e:
        print(f"Error creating block kit message: {e}")
        raise

def execute_slack_action(token, action, **kwargs):
    client = WebClient(token=token)
    try:
        print(f"Debug: Action: {action}, kwargs: {kwargs}")
        if action == "chat_postMessage":
            original_text = kwargs.get('text', '')
            if kwargs.get('name') in ["slack_send_simple_text_with_header", "slack_send_info_message", "slack_send_warning_message", "slack_send_success_message", "slack_send_two_column_message", "slack_send_image_message"]:
                template_name = f"{kwargs['name']}_template"
                print(f"Debug: Using template: {template_name}")
                if template_name in globals():
                    template = globals()[template_name]
                    try:
                        message_content = create_block_kit_message(template, **kwargs)
                        kwargs.update(message_content)
                        print(f"Debug: Updated kwargs after applying template: {kwargs}")
                    except Exception as e:
                        print(f"Error creating Block Kit message: {e}")
                        # Fallback to simple text message
                        kwargs['text'] = f"{kwargs.get('title', '')}\n\n{kwargs.get('message', original_text)}"
                        kwargs.pop('blocks', None)
                else:
                    print(f"Error: Template {template_name} not found in globals")
                    # Fallback to simple text message
                    kwargs['text'] = f"{kwargs.get('title', '')}\n\n{kwargs.get('message', original_text)}"
                    kwargs.pop('blocks', None)
            
            print(f"Debug: Sending message with final kwargs: {kwargs}")
            response = client.chat_postMessage(**kwargs)
            print(f"Debug: Slack API response: {response}")
            
            if kwargs.get('name') == "slack_send_and_pin_message":
                pin_response = client.pins_add(channel=kwargs['channel'], timestamp=response['ts'])
                return serialize_slack_response({"message": response.data, "pin": pin_response.data})
            return serialize_slack_response(response.data)
        elif action in ["conversations_list", "conversations_history", "conversations_members", "search_messages"]:
            return paginate_results(client, action, **kwargs)
        else:
            response = getattr(client, action)(**kwargs)
            return serialize_slack_response(response.data)
    except SlackApiError as e:
        error_message = str(e)
        if "missing_scope" in error_message:
            print(f"Error: The Slack app is missing required scopes. Please check the app's permissions.")
        elif "not_in_channel" in error_message:
            print(f"Error: The Slack app is not in the specified channel. Please invite the app to the channel.")
        else:
            print(f"Error executing Slack action: {e}")
        raise
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise

def paginate_results(client, action, **kwargs):
    method = getattr(client, action)
    all_results = []
    limit = int(kwargs.get('limit', 100))
    kwargs['limit'] = min(limit, 1000)  # Slack API max limit per request

    while True:
        response = method(**kwargs)
        results = response.data.get('channels') or response.data.get('messages') or response.data.get('members') or []
        all_results.extend(results)

        if len(all_results) >= limit or not response.data.get('response_metadata', {{}}).get('next_cursor'):
            break

        kwargs['cursor'] = response.data['response_metadata']['next_cursor']

    return serialize_slack_response({{"results": all_results[:limit]}})

def add_kubiya_disclaimer(text, user_email):
    disclaimer = f"\\n\\n_This message was sent using the Kubiya platform on behalf of: {{user_email}}_"
    return text + disclaimer

def convert_base64_to_file(base64_string, file_name):
    file_data = base64.b64decode(base64_string)
    with open(file_name, 'wb') as f:
        f.write(file_data)
    return file_name

if __name__ == "__main__":
    token = os.environ["SLACK_API_TOKEN"]
    user_email = os.environ.get("KUBIYA_USER_EMAIL")
    
    arg_names = {arg_names_json}
    args = {{}}
    for arg in arg_names:
        if arg in os.environ:
            args[arg] = os.environ[arg]
    
    # Handle special cases
    if 'text' in args and user_email:
        args['text'] = add_kubiya_disclaimer(args['text'], user_email)
    
    if 'blocks' in args:
        args['blocks'] = json.loads(args['blocks'])
    
    if 'file' in args and args['file'].startswith('base64:'):
        file_data = args['file'].split('base64:')[1]
        file_name = f"temp_file_{{datetime.now().strftime('%Y%m%d%H%M%S')}}"
        args['file'] = convert_base64_to_file(file_data, file_name)
    
    try:
        result = execute_slack_action(token, "{action}", **args)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error: {{e}}")
        sys.exit(1)
"""
        super().__init__(
            name=name,
            description=description,
            icon_url=SLACK_ICON_URL,
            type="docker",
            image="python:3.11",
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