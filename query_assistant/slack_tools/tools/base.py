from kubiya_sdk.tools.models import Tool, Arg, FileSpec
import json

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

class SlackSearchTool(Tool):
    def __init__(self, name, description, action, args, env=[], long_running=False, mermaid_diagram=None):
        env = ["KUBIYA_USER_EMAIL", "LLM_BASE_URL", *env]
        secrets = ["SLACK_API_TOKEN", "LLM_API_KEY"]

        arg_names_json = json.dumps([arg.name for arg in args])

        script_content = f"""
import os
import sys
import json
import logging
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import litellm
from time import time, sleep
import re
from fuzzywuzzy import fuzz
import random

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def find_channel(client, channel_input):
    logger.info(f"Attempting to find channel: {{channel_input}}")
    if not channel_input:
        logger.error("Channel input is empty")
        return None
    if channel_input.startswith('C') and len(channel_input) == 11:
        logger.info(f"Using provided channel ID directly: {{channel_input}}")
        return channel_input
    channel_input = channel_input.lstrip('#')
    try:
        for response in client.conversations_list(types="public_channel,private_channel"):
            for channel in response["channels"]:
                if channel["name"].lower() == channel_input.lower():
                    logger.info(f"Exact match found: {{channel['id']}}")
                    return channel["id"]
                elif fuzz.ratio(channel["name"].lower(), channel_input.lower()) > 80:
                    logger.info(f"Close match found: {{channel['name']}} (ID: {{channel['id']}})")
                    return channel["id"]
    except SlackApiError as e:
        logger.error(f"Error listing channels: {{e}}")
    logger.error(f"Channel not found: {{channel_input}}")
    return None

def process_time_filter(oldest_param):
    if not oldest_param:
        return None
    if oldest_param.replace('.', '').isdigit():
        return oldest_param
    time_pattern = re.match(r'(\d+)([hdmw])', oldest_param.lower())
    if time_pattern:
        amount = int(time_pattern.group(1))
        unit = time_pattern.group(2)
        if unit == 'h': seconds = 3600 * amount
        elif unit == 'd': seconds = 86400 * amount
        elif unit == 'w': seconds = 604800 * amount
        elif unit == 'm': seconds = 60 * amount
        else: return None
        current_time = time()
        target_time = current_time - seconds
        return f"{{target_time:.6f}}"
    return None

def get_thread_replies(client, channel_id, thread_ts):
    try:
        replies = []
        cursor = None
        while True:
            params = {{"channel": channel_id, "ts": thread_ts, "limit": 200}}
            if cursor: params["cursor"] = cursor
            def api_call(): return client.conversations_replies(**params)
            response = retry_with_backoff(api_call)
            thread_messages = response["messages"]
            replies_batch = thread_messages[1:] if len(thread_messages) > 1 else []
            replies.extend(replies_batch)
            if response.get("has_more", False) and response.get("response_metadata", {{}}).get("next_cursor"):
                cursor = response.get("response_metadata", {{}}).get("next_cursor")
            else:
                break
        return replies
    except Exception as e:
        logger.error(f"Error fetching replies for thread {{thread_ts}}: {{e}}")
        return []

def retry_with_backoff(func, max_retries=5, initial_delay=2, max_delay=60):
    retries, delay = 0, initial_delay
    while retries < max_retries:
        try:
            return func()
        except SlackApiError as e:
            if "ratelimited" in str(e):
                jitter = random.uniform(0, 0.1 * delay)
                sleep_time = delay + jitter
                logger.warning(f"Rate limited. Retrying in {{sleep_time:.2f}} seconds (attempt {{retries+1}}/{{max_retries}})")
                sleep(sleep_time)
                delay = min(delay * 2, max_delay)
                retries += 1
            else:
                raise
    raise Exception(f"Failed after {{max_retries}} retries due to rate limiting")

def get_channel_messages(client, channel_id, oldest):
    try:
        messages, cursor, latest = [], None, None
        while True:
            params = {{"channel": channel_id, "oldest": oldest, "limit": 250}}
            if cursor: params["cursor"] = cursor
            if latest: params["latest"] = latest
            def api_call(): return client.conversations_history(**params)
            response = retry_with_backoff(api_call)
            batch = response["messages"]
            if not batch: break
            messages.extend(batch)
            if response.get("has_more", False):
                cursor = response.get("response_metadata", {{}}).get("next_cursor")
                if not cursor and batch:
                    latest = batch[-1].get("ts")
                if len(messages) >= 50000:
                    logger.info("Reached maximum message limit (50000), stopping pagination")
                    break
            else:
                break
        logger.info(f"Total messages retrieved: {{len(messages)}}")
        processed_messages = []
        for msg in messages:
            processed_msg = {{"message": msg.get("text", ""), "timestamp": msg.get("ts", "")}}
            thread_ts = msg.get("thread_ts")
            if thread_ts and thread_ts == msg.get("ts"):
                replies = get_thread_replies(client, channel_id, thread_ts)
                processed_msg["replies"] = [{"message": r.get("text", ""), "timestamp": r.get("ts", "")} for r in replies]
            else:
                processed_msg["replies"] = []
            processed_messages.append(processed_msg)
        return processed_messages
    except SlackApiError as e:
        logger.error(f"Error fetching channel history: {{e}}")
        return []

def format_messages(messages, channel_id):
    lines = []
    for i, msg in enumerate(messages):
        link = f"https://slack.com/archives/{{channel_id}}/p{{msg['timestamp'].replace('.', '')}}"
        lines.append(f"[MSG_ID:{{i+1}}] {{msg['message']}}\\nLINK: {{link}}\\nTIMESTAMP: {{msg['timestamp']}}\\n")
        for j, r in enumerate(msg.get("replies", [])):
            r_link = f"{{link}}?thread_ts={{msg['timestamp']}}&cid={{channel_id}}"
            lines.append(f"  [REPLY_ID:{{i+1}}.{{j+1}}] {{r['message']}}\\n  LINK: {{r_link}}\\n  TIMESTAMP: {{r['timestamp']}}\\n")
    return "\\n".join(lines)

def analyze_messages_with_llm(messages, query, channel_id, oldest):
    logger.info(f"Analyzing {{len(messages)}} messages with query: {{query}}")
    messages_text = format_messages(messages, channel_id)
    if len(messages_text) > 50000:
        logger.info("Message size too large, splitting into chunks")
        blocks = messages_text.split("[MSG_ID:")[1:]
        blocks = ["[MSG_ID:" + b for b in blocks]
        chunks, chunk, MAX = [], "", 50000
        for b in blocks:
            if len(chunk) + len(b) < MAX:
                chunk += b
            else:
                chunks.append(chunk)
                chunk = b
        if chunk: chunks.append(chunk)
        all_results = []
        for i, chunk in enumerate(chunks):
            prompt = (
                "You are analyzing Slack messages to find information that answers the user's query.\\n"
                "Categorize your findings:\\n"
                "✅ Confirmed Information: directly addresses the query.\\n"
                "🟡 Possibly Related: partially matches or suggests a possible answer.\\n"
                "❌ No Match: unrelated or unclear.\\n\\n"
                "IMPORTANT: Include the message link as: 'MESSAGE_LINK: <link>'\\n\\n"
                f"Query: {{query}}\\n\\nMessages (Chunk {{i+1}}/{{len(chunks)}}):\\n{{chunk}}"
            )
            llm_messages = [
                {{"role": "system", "content": "You are a Slack message analysis assistant."}},
                {{"role": "user", "content": prompt}}
            ]
            response = litellm.completion(
                messages=llm_messages,
                model="openai/Llama-4-Scout",
                api_key=os.environ.get("LLM_API_KEY"),
                base_url=os.environ.get("LLM_BASE_URL"),
                stream=False,
                user=os.environ.get("KUBIYA_USER_EMAIL"),
                max_tokens=2048
            )
            chunk_result = response.choices[0].message.content.strip()
            all_results.append(chunk_result)
        return "\\n\\n".join([f"--- Chunk {{i+1}} ---\\n{{r}}" for i, r in enumerate(all_results)])
    else:
        prompt = (
            "You are analyzing Slack messages to find information that answers the user's query.\\n"
            "Categorize your findings:\\n"
            "✅ Confirmed Information: directly addresses the query.\\n"
            "🟡 Possibly Related: partially matches or suggests a possible answer.\\n"
            "❌ No Match: unrelated or unclear.\\n\\n"
            "IMPORTANT: Include the message link as: 'MESSAGE_LINK: <link>'\\n\\n"
            f"Query: {{query}}\\n\\nMessages:\\n{{messages_text}}"
        )
        response = litellm.completion(
            messages=[{{"role": "system", "content": "You are a Slack message analysis assistant."}}, {{"role": "user", "content": prompt}}],
            model="openai/Llama-4-Scout",
            api_key=os.environ.get("LLM_API_KEY"),
            base_url=os.environ.get("LLM_BASE_URL"),
            stream=False,
            user=os.environ.get("KUBIYA_USER_EMAIL"),
            max_tokens=2048
        )
        return response.choices[0].message.content.strip()

def execute_slack_action(token, action, operation, **kwargs):
    client = WebClient(token=token)
    logger.info(f"Executing Slack search action with params: {{kwargs}}")
    channel = kwargs.get('channel')
    query = kwargs.get('query')
    oldest = kwargs.get('oldest', '24h')
    if not channel:
        return {{"success": False, "error": "Channel parameter is required"}}
    channel_id = find_channel(client, channel)
    if not channel_id:
        return {{"success": False, "error": f"Channel not found: {{channel}}"}}
    oldest_ts = process_time_filter(oldest)
    if not oldest_ts:
        return {{"success": False, "answer": "Invalid time filter format. Use format like '1h', '2d', '1w', or '30m'"}}
    messages = get_channel_messages(client, channel_id, oldest_ts)
    if not messages:
        return {{"success": True, "answer": f"No messages found in the last {{oldest}}."}}
    logger.info(f"Found {{len(messages)}} messages to analyze")
    answer = analyze_messages_with_llm(messages, query, channel_id, oldest)
    return {{"success": True, "answer": answer}}

if __name__ == "__main__":
    token = os.environ.get("SLACK_API_TOKEN")
    if not token:
        print(json.dumps({{"success": False, "error": "SLACK_API_TOKEN is not set"}}))
        sys.exit(1)
    arg_names = {arg_names_json}
    args = {{}}
    for arg in arg_names:
        if arg in os.environ:
            args[arg] = os.environ[arg]
    result = execute_slack_action(token, "{action}", "{name}", **args)
    print(json.dumps(result))
"""
        super().__init__(
            name=name,
            description=description,
            icon_url=SLACK_ICON_URL,
            type="docker",
            image="python:3.11-slim",
            content="pip install -q slack-sdk fuzzywuzzy python-Levenshtein litellm tenacity > /dev/null 2>&1 && python /tmp/script.py",
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

class SlackSummaryTool(Tool):
    def __init__(self, name, description, action, args, env=[], long_running=False, mermaid_diagram=None):
        # Make sure we include the required environment variables
        env = ["KUBIYA_USER_EMAIL", "SLACK_CHANNEL_ID", "SLACK_THREAD_TS", *env]
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
logger = logging.getLogger(__name__)

def process_thread_messages(messages):
    logger.info(f"Processing {{len(messages)}} thread messages")
    
    processed_messages = []
    
    for msg in messages:
        processed_msg = {{
            "text": msg.get("text", ""),
            "user": msg.get("user", ""),
            "timestamp": msg.get("ts", ""),
            "thread_ts": msg.get("thread_ts", "")
        }}
        
        # Add any attachments if present
        if "attachments" in msg:
            processed_msg["attachments"] = msg.get("attachments")
            
        # Add any files if present
        if "files" in msg:
            processed_msg["files"] = [
                {{
                    "name": file.get("name", ""),
                    "mimetype": file.get("mimetype", ""),
                    "url": file.get("url_private", "")
                }}
                for file in msg.get("files", [])
            ]
        
        processed_messages.append(processed_msg)
    
    return processed_messages

def execute_slack_action(token, action, operation, **kwargs):
    client = WebClient(token=token)
    logger.info(f"Executing Slack action: {{action}} for operation: {{operation}}")
    logger.info(f"Action parameters: {{kwargs}}")
    
    # Get required environment variables
    channel_id = os.environ.get("SLACK_CHANNEL_ID")
    thread_ts = os.environ.get("SLACK_THREAD_TS")
    
    logger.info(f"Using channel_id: {{channel_id}}, thread_ts: {{thread_ts}}")
    
    if not channel_id or not thread_ts:
        return {{"success": False, "error": "Missing required environment variables: SLACK_CHANNEL_ID and/or SLACK_THREAD_TS"}}
    
    try:
        # Get thread messages
        response = client.conversations_replies(
            channel=channel_id,
            ts=thread_ts,
            limit=1000  # Get as many messages as possible
        )
        
        thread_messages = response["messages"]
        logger.info(f"Retrieved {{len(thread_messages)}} messages from thread")
        
        # Use pagination if needed
        while response.get("has_more", False) and response.get("response_metadata", {{}}).get("next_cursor"):
            cursor = response.get("response_metadata", {{}}).get("next_cursor")
            response = client.conversations_replies(
                channel=channel_id,
                ts=thread_ts,
                cursor=cursor,
                limit=1000
            )
            thread_messages.extend(response["messages"])
            logger.info(f"Retrieved additional {{len(response['messages'])}} messages from thread")
        
        if not thread_messages:
            return {{"success": True, "thread_messages": [], "message": "No messages found in this thread."}}
        
        # Process the thread messages
        processed_messages = process_thread_messages(thread_messages)
        
        # Create a thread URL for reference
        thread_url = f"https://slack.com/archives/{{channel_id}}/p{{thread_ts.replace('.', '')}}"
        
        return {{
            "success": True,
            "thread_messages": processed_messages,
            "thread_url": thread_url,
            "message_count": len(processed_messages)
        }}
        
    except SlackApiError as e:
        error_message = str(e)
        logger.error(f"Error retrieving thread messages: {{error_message}}")
        return {{"success": False, "error": error_message}}

if __name__ == "__main__":
    token = os.environ.get("SLACK_API_TOKEN")
    if not token:
        logger.error("SLACK_API_TOKEN is not set")
        print(json.dumps({{"success": False, "error": "SLACK_API_TOKEN is not set"}}))
        sys.exit(1)

    logger.info("Starting Slack thread retrieval...")
    arg_names = {arg_names_json}
    args = {{}}
    for arg in arg_names:
        if arg in os.environ:
            args[arg] = os.environ[arg]
    
    result = execute_slack_action(token, "{action}", "{name}", **args)
    logger.info("Slack thread retrieval completed")
    print(json.dumps(result))
"""
        super().__init__(
            name=name,
            description=description,
            icon_url=SLACK_ICON_URL,
            type="docker",
            image="python:3.11-slim",
            content="pip install -q slack-sdk > /dev/null 2>&1 && python /tmp/script.py",
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