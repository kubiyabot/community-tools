from kubiya_sdk.tools.models import Tool, Arg, FileSpec
import json
import litellm

SLACK_ICON_URL = "https://a.slack-edge.com/80588/marketing/img/icons/icon_slack_hash_colored.png"

class SlackTool(Tool):
    def __init__(self, name, description, action, args, env=[], long_running=False, mermaid_diagram=None):
        env = ["KUBIYA_USER_EMAIL", *env]
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

def create_block_kit_message(text, kubiya_user_email):
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
        }}
    ]

def find_channel(client, channel_input):
    logger.info(f"Attempting to find channel: {{channel_input}}")
    
    if not channel_input:
        logger.error("Channel input is empty")
        return None
    
    # If it's already a valid channel ID (starts with C and is 11 characters long), use it directly
    if channel_input.startswith('C') and len(channel_input) == 11:
        logger.info(f"Using provided channel ID directly: {{channel_input}}")
        return channel_input
    
    # Remove '#' if present
    channel_input = channel_input.lstrip('#')
    
    # Try to find the channel by name
    try:
        for response in client.conversations_list(types="public_channel,private_channel"):
            for channel in response["channels"]:
                # Try exact match first
                if channel["name"].lower() == channel_input.lower():
                    logger.info(f"Exact match found: {{channel['id']}}")
                    return channel["id"]
                # Fall back to fuzzy match if no exact match found
                elif fuzz.ratio(channel["name"].lower(), channel_input.lower()) > 80:
                    logger.info(f"Close match found: {{channel['name']}} (ID: {{channel['id']}})")
                    return channel["id"]
    except SlackApiError as e:
        logger.error(f"Error listing channels: {{e}}")

    logger.error(f"Channel not found: {{channel_input}}")
    return None

def send_slack_message(client, channel, text):
    logger.info(f"Starting to send Slack message to: {{channel}}")
    
    if not channel:
        logger.error("Channel parameter is missing or empty")
        return {{"success": False, "error": "Channel parameter is missing or empty"}}
    
    channel_id = find_channel(client, channel)
    if not channel_id:
        return {{"success": False, "error": f"Channel not found: {{channel}}"}}

    try:
        kubiya_user_email = os.environ.get("KUBIYA_USER_EMAIL", "Unknown User")
        
        blocks = create_block_kit_message(text, kubiya_user_email)
        
        fallback_text = f"{{text}}\\n\\n_This message was sent on behalf of <@{{kubiya_user_email}}> using the Kubiya AI platform_"

        logger.info(f"Attempting to send Block Kit message to channel ID: {{channel_id}}")
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

def process_slack_messages(messages, is_reply=False):
    logger.info(f"Processing {{len(messages)}} messages")
    
    # Print each message individually instead of joining
    for msg in messages:
        processed_msg = {{
            "message": msg.get("text", ""),
            "timestamp": msg.get("ts", "")
        }}
        
        # Only include reply_count for main messages, not for replies
        if not is_reply:
            processed_msg["reply_count"] = msg.get("reply_count", 0)
            
        print(json.dumps(processed_msg))  # Print each message directly
    
    return "Messages printed individually"  # Return a placeholder

def execute_slack_action(token, action, operation, **kwargs):
    client = WebClient(token=token)
    logger.info(f"Executing Slack action: {{action}}")
    logger.info(f"Action parameters: {{kwargs}}")

    try:
        # Handle channel resolution if channel parameter is provided
        if 'channel' in kwargs and operation != "slack_send_message_to_predefined_channel":
            channel_id = find_channel(client, kwargs['channel'])
            if not channel_id:
                return {{"success": False, "error": f"Channel not found: {{kwargs['channel']}}"}}
            kwargs['channel'] = channel_id

        # Handle channel requirement for operations that need it
        channel_required_actions = [
            "chat_postMessage", "conversations_invite", "conversations_info",
            "reactions_add", "chat_delete", "chat_update", "reactions_remove",
            "conversations_history", "conversations_replies"
        ]
        
        if action in channel_required_actions and operation != "slack_send_message_to_predefined_channel":
            if 'channel' not in kwargs:
                logger.error("Channel parameter is required for this operation")
                return {{"success": False, "error": "Channel parameter is required"}}
            
            channel_id = find_channel(client, kwargs['channel'])
            if not channel_id:
                return {{"success": False, "error": f"Channel not found: {{kwargs['channel']}}"}}
            kwargs['channel'] = channel_id

        if action == "chat_postMessage":
            if 'text' not in kwargs:
                logger.error(f"Missing required parameters for chat_postMessage. Received: {{kwargs}}")
                return {{"success": False, "error": "Missing required parameters for chat_postMessage"}}
            if operation == "slack_send_message_to_predefined_channel":
                result = send_slack_message(client, os.environ["NOTIFICATION_CHANNEL"], kwargs['text'])
            else:
                result = send_slack_message(client, kwargs['channel'], kwargs['text'])    
        elif action in ["conversations_history", "conversations_replies"]:
            if action == "conversations_history" and 'oldest' in kwargs:
                oldest_param = kwargs['oldest']
                if isinstance(oldest_param, str):
                    from time import time
                    import re
                    
                    time_pattern = re.match(r'(\d+)([hdm])', oldest_param.lower())
                    if time_pattern:
                        amount = int(time_pattern.group(1))
                        unit = time_pattern.group(2)
                        seconds = {{'h': 3600, 'd': 86400, 'm': 60}}[unit]
                        current_time = time()
                        offset = amount * seconds
                        target_time = current_time - offset
                        kwargs['oldest'] = f"{{target_time:.6f}}"  # Format with exactly 6 decimal places
                        logger.info(f"Time conversion: current={{current_time}}, offset={{offset}}, target={{target_time}}, oldest_param={{kwargs['oldest']}}")
            
            method = getattr(client, action)
            response = method(**kwargs)
            if 'messages' in response.data:
                result = process_slack_messages(
                    response.data['messages'], 
                    is_reply=(action == "conversations_replies")
                )
                result = {{"success": True, "result": result}}
                logger.info("Messages processed successfully")
            else:
                result = {{"success": True, "result": response.data}}
        else:
            logger.info("Executing action: %s", action)
            method = getattr(client, action)
            
            response = method(**kwargs)
            result = {{"success": True, "result": response.data}}
            if 'ts' in response.data:
                result['thread_ts'] = response.data['ts']
        
        logger.info("Action completed successfully")
        return result
    except Exception as e:
        logger.error(f"Unexpected error: {{str(e)}}")
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
    
    result = execute_slack_action(token, "{action}", "{name}", **args)
    logger.info("Slack action execution completed")
    print(json.dumps(result))
"""
        super().__init__(
            name=name,
            description=description,
            icon_url=SLACK_ICON_URL,
            type="docker",
            image="python:3.11-slim",
            content="pip install -q slack-sdk fuzzywuzzy python-Levenshtein > /dev/null 2>&1 && python /tmp/script.py",
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

class SlackSearchTool(SlackTool):
    def __init__(self, name, description, action, args):
        script_content = """
import os
import sys
import json
import logging
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import litellm

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_message_relevance(query, message_text):
    try:
        messages = [
            {"role": "system", "content": "You are a helpful assistant that determines if a Slack message is relevant to a user's query. Respond with only 'yes' or 'no'."},
            {"role": "user", "content": f"Query: {query}\\nMessage: {message_text}\\nIs this message relevant to the query? Answer only 'yes' or 'no'."}
        ]
        
        response = litellm.completion(
            messages=messages,
            model="openai/Llama-4-Scout",
            api_key=os.environ.get("LITELLM_API_KEY"),
            base_url=os.environ.get("LITELLM_API_BASE"),
            max_tokens=10
        )
        
        answer = response.choices[0].message.content.strip().lower()
        return answer == "yes"
    except Exception as e:
        logger.error(f"Error checking message relevance: {e}")
        return False

def get_thread_replies(client, channel_id, thread_ts, query):
    try:
        response = client.conversations_replies(
            channel=channel_id,
            ts=thread_ts
        )
        
        relevant_replies = []
        for reply in response["messages"][1:]:  # Skip the parent message
            if check_message_relevance(query, reply.get("text", "")):
                relevant_replies.append({
                    "text": reply.get("text", ""),
                    "ts": reply.get("ts", ""),
                    "is_reply": True
                })
        
        return relevant_replies
    except SlackApiError as e:
        logger.error(f"Error fetching thread replies: {e}")
        return []

def search_channel_history(client, channel_id, query, cursor=None):
    batch_size = 20
    try:
        params = {
            "channel": channel_id,
            "limit": batch_size
        }
        if cursor:
            params["cursor"] = cursor
            
        response = client.conversations_history(**params)
        
        relevant_messages = []
        for msg in response["messages"]:
            if check_message_relevance(query, msg.get("text", "")):
                message_data = {
                    "text": msg.get("text", ""),
                    "ts": msg.get("ts", ""),
                    "thread_ts": msg.get("thread_ts", ""),
                    "replies": []
                }
                
                # If message has replies (thread), check them too
                if msg.get("reply_count", 0) > 0:
                    thread_replies = get_thread_replies(client, channel_id, msg["ts"], query)
                    if thread_replies:
                        message_data["replies"] = thread_replies
                
                relevant_messages.append(message_data)
                
        result = {
            "messages": relevant_messages,
            "has_more": response["has_more"],
            "next_cursor": response.get("response_metadata", {}).get("next_cursor")
        }
        
        return result
        
    except SlackApiError as e:
        logger.error(f"Error searching channel history: {e}")
        return None

def execute_search(token, channel, query):
    client = WebClient(token=token)
    cursor = None
    all_relevant_messages = []
    
    while True:
        result = search_channel_history(client, channel, query, cursor)
        if not result:
            break
            
        all_relevant_messages.extend(result["messages"])
        
        # Stop if we have enough messages or there are no more to fetch
        if not result["has_more"] or len(all_relevant_messages) >= 5:
            break
            
        cursor = result["next_cursor"]
    
    # Format the final response
    formatted_messages = []
    for msg in all_relevant_messages:
        message_info = {
            "message": msg["text"],
            "timestamp": msg["ts"]
        }
        
        if msg["replies"]:
            message_info["thread_replies"] = [
                {"message": reply["text"], "timestamp": reply["ts"]}
                for reply in msg["replies"]
            ]
            
        formatted_messages.append(message_info)
    
    return {"success": True, "messages": formatted_messages}

if __name__ == "__main__":
    token = os.environ.get("SLACK_API_TOKEN")
    channel = os.environ.get("channel")
    query = os.environ.get("query")
    
    if not all([token, channel, query]):
        print(json.dumps({"success": False, "error": "Missing required environment variables"}))
        sys.exit(1)
    
    result = execute_search(token, channel, query)
    print(json.dumps(result))
"""
        
        super().__init__(
            name=name,
            description=description,
            action=action,
            args=args,
            env=["LITELLM_API_KEY", "LITELLM_API_BASE"],
            with_files=[
                FileSpec(
                    destination="/tmp/script.py",
                    content=script_content,
                )
            ],
        )