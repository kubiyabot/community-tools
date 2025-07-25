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
from datetime import datetime
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import litellm
from time import time, sleep
import re
from fuzzywuzzy import fuzz
import random

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Cache for user info to avoid duplicate API calls
user_cache = {{}}

def get_user_info(client, user_id):
    \"\"\"Get user information and cache it to avoid duplicate API calls\"\"\"
    if not user_id:
        return {{"name": "Unknown User", "real_name": "Unknown User", "display_name": "Unknown User"}}
    
    # Check cache first
    if user_id in user_cache:
        return user_cache[user_id]
    
    try:
        response = client.users_info(user=user_id)
        user_info = response["user"]
        
        # Extract name information
        name = user_info.get("name", "Unknown User")
        real_name = user_info.get("real_name", name)
        display_name = user_info.get("profile", {{}}).get("display_name", "")
        
        # Use display name if available, otherwise real name, otherwise username
        user_display_name = display_name if display_name else (real_name if real_name else name)
        
        user_data = {{
            "name": name,
            "real_name": real_name,
            "display_name": user_display_name
        }}
        
        # Cache the result
        user_cache[user_id] = user_data
        logger.info(f"Retrieved user info for {{user_id}}: {{user_display_name}}")
        
        return user_data
        
    except SlackApiError as e:
        logger.warning(f"Could not retrieve user info for {{user_id}}: {{e}}")
        # Cache the unknown user to avoid repeated failed calls
        user_data = {{"name": "Unknown User", "real_name": "Unknown User", "display_name": "Unknown User"}}
        user_cache[user_id] = user_data
        return user_data

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

def process_time_filter(oldest_param):
    if not oldest_param:
        return None
        
    # Handle direct Unix timestamp
    if oldest_param.replace('.', '').isdigit():
        return oldest_param
        
    time_pattern = re.match(r'(\d+)([hdmw])', oldest_param.lower())
    if time_pattern:
        amount = int(time_pattern.group(1))
        unit = time_pattern.group(2)
        
        # Calculate seconds based on unit
        if unit == 'h':
            seconds = 3600 * amount
        elif unit == 'd':
            seconds = 86400 * amount
        elif unit == 'w':
            seconds = 604800 * amount
        elif unit == 'm':
            seconds = 60 * amount
        else:
            return None
            
        # Get current time
        current_time = time()
        target_time = current_time - seconds
        
        # Format with 6 decimal places
        return f"{{target_time:.6f}}"
    
    return None

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

def retry_with_backoff(func, max_retries=5, initial_delay=2, max_delay=60):
    retries = 0
    delay = initial_delay
    
    while retries < max_retries:
        try:
            return func()
        except SlackApiError as e:
            error_message = str(e)
            
            # Check if rate limited
            if "ratelimited" in error_message:
                # Add jitter to avoid thundering herd problem
                jitter = random.uniform(0, 0.1 * delay)
                sleep_time = delay + jitter
                
                logger.warning(f"Rate limited. Retrying in {{sleep_time:.2f}} seconds (attempt {{retries+1}}/{{max_retries}})")
                sleep(sleep_time)
                
                # Exponential backoff
                delay = min(delay * 2, max_delay)
                retries += 1
            else:
                # If not rate limited, re-raise the exception
                raise
    
    # If we've exhausted retries, raise the last exception
    raise Exception(f"Failed after {{max_retries}} retries due to rate limiting")

def get_channel_messages(client, channel_id, oldest):
    try:
        messages = []
        cursor = None
        latest = None  # For time-based pagination
        
        # Get today's date
        today_date = datetime.now().strftime("%Y-%m-%d")
        
        # Use pagination to get all messages
        while True:
            params = {{
                "channel": channel_id,
                "oldest": oldest,
                "limit": 250  # Recommended by Slack API
            }}
            
            # Add cursor for pagination if we have one
            if cursor:
                params["cursor"] = cursor
            
            # Add latest timestamp for time-based pagination if we have one
            if latest:
                params["latest"] = latest
            
            # Use retry with backoff for API call
            def api_call():
                return client.conversations_history(**params)
                
            response = retry_with_backoff(api_call)
            batch = response["messages"]
            
            if not batch:
                logger.info("No messages returned in this batch")
                break
                
            messages.extend(batch)
            
            # Check if there are more messages to fetch via cursor
            if response.get("has_more", False) and response.get("response_metadata", {{}}).get("next_cursor"):
                cursor = response.get("response_metadata", {{}}).get("next_cursor")
                latest = None  # Reset latest when using cursor
            # If has_more is true but no cursor, use time-based pagination
            elif response.get("has_more", False):
                # Get the timestamp of the oldest message in this batch
                if batch:
                    latest = batch[-1].get("ts")
                    cursor = None  # Reset cursor when using time-based pagination
                else:
                    break
            else:
                break
                
            # Safety limit to prevent excessive API calls
            if len(messages) >= 50000:
                logger.info(f"Reached maximum message limit (50000), stopping pagination")
                break
        
        logger.info(f"Total messages retrieved: {{len(messages)}}")
        
        # Process messages for LLM analysis
        processed_messages = []
        
        for msg in messages:
            # Get user information
            user_id = msg.get("user", "")
            user_info = get_user_info(client, user_id)
            
            # Convert timestamp to readable date
            message_ts = msg.get("ts", "")
            message_date = "Unknown Date"
            if message_ts:
                try:
                    message_datetime = datetime.fromtimestamp(float(message_ts))
                    message_date = message_datetime.strftime("%Y-%m-%d")
                except (ValueError, TypeError):
                    logger.warning(f"Could not parse timestamp: {{message_ts}}")
            
            processed_msg = {{
                "message": msg.get("text", ""),
                "timestamp": message_ts,
                "user_id": user_id,
                "user_name": user_info["display_name"],
                "today_date": today_date,
                "message_date": message_date
            }}

            # Check if message has a thread
            thread_ts = msg.get("thread_ts")
            if thread_ts and thread_ts == msg.get("ts"):
                replies = get_thread_replies(client, channel_id, thread_ts)
                
                # Attach replies under parent message
                processed_msg["replies"] = []
                for reply in replies:
                    reply_user_id = reply.get("user", "")
                    reply_user_info = get_user_info(client, reply_user_id)
                    
                    # Convert reply timestamp to readable date
                    reply_ts = reply.get("ts", "")
                    reply_date = "Unknown Date"
                    if reply_ts:
                        try:
                            reply_datetime = datetime.fromtimestamp(float(reply_ts))
                            reply_date = reply_datetime.strftime("%Y-%m-%d")
                        except (ValueError, TypeError):
                            logger.warning(f"Could not parse reply timestamp: {{reply_ts}}")
                    
                    processed_msg["replies"].append({{
                        "message": reply.get("text", ""),
                        "timestamp": reply_ts,
                        "user_id": reply_user_id,
                        "user_name": reply_user_info["display_name"],
                        "today_date": today_date,
                        "message_date": reply_date
                    }})
            else:
                processed_msg["replies"] = []  # no replies

            processed_messages.append(processed_msg)
            
        return processed_messages
        
    except SlackApiError as e:
        logger.error(f"Error fetching channel history: {{e}}")
        return []

def get_thread_replies(client, channel_id, thread_ts):
    try:
        replies = []
        cursor = None
        while True:
            params = {{
                "channel": channel_id,
                "ts": thread_ts,
                "limit": 200
            }}
            if cursor:
                params["cursor"] = cursor
            
            # Use retry with backoff for API call
            def api_call():
                return client.conversations_replies(**params)
                
            response = retry_with_backoff(api_call)
            thread_messages = response["messages"]
            
            # Skip the first message (it's the parent)
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
        
def analyze_messages_with_llm(messages, query, channel_id):
    try:
        logger.info(f"Analyzing {{len(messages)}} messages with query: {{query}}")

        def format_messages(messages):
            lines = []
            for i, msg in enumerate(messages):
                # Create a message link using timestamp and channel ID
                message_link = f"https://slack.com/archives/{{channel_id}}/p{{msg['timestamp'].replace('.', '')}}"
                # Include a unique message ID and make the link more prominent, now with user name
                user_name = msg.get('user_name', 'Unknown User')
                lines.append(f"[MSG_ID:{{i+1}}] {{user_name}}: {{msg['message']}}\\nLINK: {{message_link}}\\nTIMESTAMP: {{msg['timestamp']}}\\n")
                
                for j, reply in enumerate(msg.get("replies", [])):
                    # Create a reply link using thread timestamp and reply timestamp
                    reply_link = f"https://slack.com/archives/{{channel_id}}/p{{msg['timestamp'].replace('.', '')}}?thread_ts={{msg['timestamp']}}&cid={{channel_id}}"
                    # Include a unique reply ID and make the link more prominent, now with user name
                    reply_user_name = reply.get('user_name', 'Unknown User')
                    lines.append(f"  [REPLY_ID:{{i+1}}.{{j+1}}] {{reply_user_name}}: {{reply['message']}}\\n  LINK: {{reply_link}}\\n  TIMESTAMP: {{reply['timestamp']}}\\n")
            return "\\n".join(lines)

        # Format all messages first
        messages_text = format_messages(messages)
        
        # Check if we need to chunk the messages
        MAX_CHUNK_SIZE = 50000  # Conservative limit for API request
        
        if len(messages_text) > MAX_CHUNK_SIZE:
            logger.info(f"Messages text too large ({{len(messages_text)}} chars), processing in chunks")
            
            # Split by message boundaries (each message starts with [MSG_ID:)
            message_blocks = messages_text.split("[MSG_ID:")
            
            # First element is empty, skip it
            if message_blocks and not message_blocks[0].strip():
                message_blocks = message_blocks[1:]
                
            # Add the prefix back to each message
            message_blocks = ["[MSG_ID:" + block if i > 0 else block for i, block in enumerate(message_blocks)]
            
            # Create chunks of messages
            chunks = []
            current_chunk = ""
            
            for block in message_blocks:
                if len(current_chunk) + len(block) < MAX_CHUNK_SIZE:
                    current_chunk += block
                else:
                    if current_chunk:
                        chunks.append(current_chunk)
                    current_chunk = block
                    
            # Add the last chunk if it's not empty
            if current_chunk:
                chunks.append(current_chunk)
                
            logger.info(f"Split messages into {{len(chunks)}} chunks")
            
            # Process each chunk separately
            all_results = []
            for i, chunk in enumerate(chunks):
                logger.info(f"Processing chunk {{i+1}}/{{len(chunks)}}")
                
                # Create prompt for this chunk
                chunk_prompt = (
                    "You are analyzing Slack messages to find information that answers the user's query. "
                    "Focus on finding the most relevant and accurate information from the messages provided. "
                    "If multiple messages contain relevant information, synthesize them into a coherent answer. "
                    "\\n\\n"
                    "IMPORTANT: At the end of your answer, you MUST include the EXACT link of the SPECIFIC message "
                    "that contains the most relevant information. Use the format: 'MESSAGE_LINK: <exact link>'. "
                    "Do not modify or reconstruct the link - copy it exactly as provided in the message data. "
                    "Each message has a unique MSG_ID or REPLY_ID - reference this ID when citing information. "
                    "\\n\\n"
                    "Answers may appear in a reply to an earlier message, or as a separate message posted later in the channel. "
                    "If you cannot find a clear answer in the provided messages, state that clearly and suggest what kind of information might help. "
                    "\\n\\n"
                    f"Query: {{query}}\\n\\n"
                    f"Messages (Chunk {{i+1}} of {{len(chunks)}}):\\n{{chunk}}"
                )
                
                chunk_messages = [
                    {{"role": "system", "content": "You are a specialized assistant for Slack message analysis. Your task is to carefully examine Slack messages, identify relevant information that answers the user's query, and provide clear, concise responses. Pay special attention to message timestamps as they may be needed for thread identification."}},
                    {{"role": "user", "content": chunk_prompt}}
                ]
                
                base_url = os.environ.get("LLM_BASE_URL")
                
                response = litellm.completion(
                    messages=chunk_messages,
                    model="openai/Llama-4-Scout",
                    api_key=os.environ.get("LLM_API_KEY"),
                    base_url=base_url,
                    stream=False,
                    user=os.environ.get("KUBIYA_USER_EMAIL"),
                    max_tokens=2048,
                    temperature=0.7,
                    top_p=0.1,
                    presence_penalty=0.0,
                    frequency_penalty=0.0,
                    timeout=30,
                )
                
                chunk_result = response.choices[0].message.content.strip()
                all_results.append(chunk_result)
            
            # Combine results
            combined_result = "I've analyzed all messages in chunks due to the large volume. Here's what I found:\\n\\n"
            for i, result in enumerate(all_results):
                combined_result += f"--- Chunk {{i+1}} Results ---\\n{{result}}\\n\\n"
                
            return combined_result
        else:
            # Process normally if size is manageable
            prompt = (
                "You are analyzing Slack messages to find information that answers the user's query. "
                "Focus on finding the most relevant and accurate information from the messages provided. "
                "If multiple messages contain relevant information, synthesize them into a coherent answer. "
                "\\n\\n"
                "IMPORTANT: At the end of your answer, you MUST include the EXACT link of the SPECIFIC message "
                "that contains the most relevant information. Use the format: 'MESSAGE_LINK: <exact link>'. "
                "Do not modify or reconstruct the link - copy it exactly as provided in the message data. "
                "Each message has a unique MSG_ID or REPLY_ID - reference this ID when citing information. "
                "\\n\\n"
                "Answers may appear in a reply to an earlier message, or as a separate message posted later in the channel. "
                "If you cannot find a clear answer in the provided messages, state that clearly and suggest what kind of information might help. "
                "\\n\\n"
                f"Query: {{query}}\\n\\n"
                f"Messages:\\n{{messages_text}}"
            )

            litellm.request_timeout = 30
            litellm.num_retries = 3

            llm_messages = [
                {{"role": "system", "content": "You are a specialized assistant for Slack message analysis. Your task is to carefully examine Slack messages, identify relevant information that answers the user's query, and provide clear, concise responses. Pay special attention to message timestamps as they may be needed for thread identification."}},
                {{"role": "user", "content": prompt}}
            ]

            base_url = os.environ.get("LLM_BASE_URL")

            response = litellm.completion(
                messages=llm_messages,
                model="openai/Llama-4-Scout",
                api_key=os.environ.get("LLM_API_KEY"),
                base_url=base_url,
                stream=False,
                user=os.environ.get("KUBIYA_USER_EMAIL"),
                max_tokens=2048,
                temperature=0.7,
                top_p=0.1,
                presence_penalty=0.0,
                frequency_penalty=0.0,
                timeout=30,
            )

            answer = response.choices[0].message.content.strip()
            logger.info("LLM response received successfully")
            return answer

    except litellm.Timeout:
        logger.error("LLM request timed out")
        return "The LLM analysis timed out. Please try again later."

    except Exception as e:
        logger.error(f"Error analyzing messages: {{str(e)}}")
        return f"Error during LLM analysis: {{str(e)}}"

def execute_slack_action(token, action, operation, **kwargs):
    # Print current date and time at the beginning
    current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"Starting Slack search execution at: {{current_datetime}}")
    print(f"Current date and time: {{current_datetime}}")
    
    client = WebClient(token=token)
    logger.info(f"Executing Slack search action with params: {{kwargs}}")
    
    channel = kwargs.get('channel')
    query = kwargs.get('query')
    oldest = kwargs.get('oldest', '24h')  # Default to last 24 hours
    
    if not channel:
        return {{"success": False, "error": "Channel parameter is required"}}
    
    channel_id = find_channel(client, channel)
    if not channel_id:
        return {{"success": False, "error": f"Channel not found: {{channel}}"}}
    
    # Process time filter
    oldest_ts = process_time_filter(oldest)
    if not oldest_ts:
        return {{"success": False, "answer": "Invalid time filter format. Use format like '1h', '2d', '1w', or '30m'"}}
    
    logger.info(f"Fetching messages from channel {{channel_id}} since {{oldest_ts}}")
    
    # Get messages
    messages = get_channel_messages(client, channel_id, oldest_ts)
    
    if not messages:
        return {{"success": True, "answer": "No messages found in the specified time period"}}
    
    logger.info(f"Found {{len(messages)}} messages to analyze")
    
    # Get answer from LLM
    answer = analyze_messages_with_llm(messages, query, channel_id)
    
    return {{
        "success": True,
        "answer": answer
    }}

if __name__ == "__main__":
    token = os.environ.get("SLACK_API_TOKEN")
    if not token:
        logger.error("SLACK_API_TOKEN is not set")
        print(json.dumps({{"success": False, "error": "SLACK_API_TOKEN is not set"}}))
        sys.exit(1)

    logger.info("Starting Slack search execution...")
    arg_names = {arg_names_json}
    args = {{}}
    for arg in arg_names:
        if arg in os.environ:
            args[arg] = os.environ[arg]
    
    result = execute_slack_action(token, "{action}", "{name}", **args)
    logger.info("Slack search execution completed")
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
from datetime import datetime
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Cache for user info to avoid duplicate API calls
user_cache = {{}}

def get_user_info(client, user_id):
    \"\"\"Get user information and cache it to avoid duplicate API calls\"\"\"
    if not user_id:
        return {{"name": "Unknown User", "real_name": "Unknown User"}}
    
    # Check cache first
    if user_id in user_cache:
        return user_cache[user_id]
    
    try:
        response = client.users_info(user=user_id)
        user_info = response["user"]
        
        # Extract name information
        name = user_info.get("name", "Unknown User")
        real_name = user_info.get("real_name", name)
        display_name = user_info.get("profile", {{}}).get("display_name", "")
        
        # Use display name if available, otherwise real name, otherwise username
        user_display_name = display_name if display_name else (real_name if real_name else name)
        
        user_data = {{
            "name": name,
            "real_name": real_name,
            "display_name": user_display_name
        }}
        
        # Cache the result
        user_cache[user_id] = user_data
        logger.info(f"Retrieved user info for {{user_id}}: {{user_display_name}}")
        
        return user_data
        
    except SlackApiError as e:
        logger.warning(f"Could not retrieve user info for {{user_id}}: {{e}}")
        # Cache the unknown user to avoid repeated failed calls
        user_data = {{"name": "Unknown User", "real_name": "Unknown User", "display_name": "Unknown User"}}
        user_cache[user_id] = user_data
        return user_data

def process_thread_messages(client, messages):
    logger.info(f"Processing {{len(messages)}} thread messages")
    
    processed_messages = []
    
    for msg in messages:
        user_id = msg.get("user", "")
        user_info = get_user_info(client, user_id)
        
        processed_msg = {{
            "text": msg.get("text", ""),
            "user_id": user_id,
            "user_name": user_info["display_name"],
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
    # Print current date and time at the beginning
    current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"Starting Slack thread retrieval at: {{current_datetime}}")
    print(f"Current date and time: {{current_datetime}}")
    
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
        processed_messages = process_thread_messages(client, thread_messages)
        
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

# class SlackOutOfOfficeTool(Tool):
#     def __init__(self, name, description, action, args, env=[], long_running=False, mermaid_diagram=None):
#         env = ["KUBIYA_USER_EMAIL", "LLM_BASE_URL", *env]
#         secrets = ["SLACK_API_TOKEN", "LLM_API_KEY"]
        
#         arg_names_json = json.dumps([arg.name for arg in args])
        
#         script_content = f"""
# import os
# import sys
# import json
# import logging
# from datetime import datetime
# from slack_sdk import WebClient
# from slack_sdk.errors import SlackApiError
# import litellm
# from time import time, sleep
# import re
# from fuzzywuzzy import fuzz
# import random

# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# logger = logging.getLogger(__name__)

# # Cache for user info to avoid duplicate API calls
# user_cache = {{}}

# def get_user_info(client, user_id):
#     \"\"\"Get user information and cache it to avoid duplicate API calls\"\"\"
#     if not user_id:
#         return {{"name": "Unknown User", "real_name": "Unknown User", "display_name": "Unknown User"}}
    
#     # Check cache first
#     if user_id in user_cache:
#         return user_cache[user_id]
    
#     try:
#         response = client.users_info(user=user_id)
#         user_info = response["user"]
        
#         # Extract name information
#         name = user_info.get("name", "Unknown User")
#         real_name = user_info.get("real_name", name)
#         display_name = user_info.get("profile", {{}}).get("display_name", "")
        
#         # Use display name if available, otherwise real name, otherwise username
#         user_display_name = display_name if display_name else (real_name if real_name else name)
        
#         user_data = {{
#             "name": name,
#             "real_name": real_name,
#             "display_name": user_display_name
#         }}
        
#         # Cache the result
#         user_cache[user_id] = user_data
#         logger.info(f"Retrieved user info for {{user_id}}: {{user_display_name}}")
        
#         return user_data
        
#     except SlackApiError as e:
#         logger.warning(f"Could not retrieve user info for {{user_id}}: {{e}}")
#         # Cache the unknown user to avoid repeated failed calls
#         user_data = {{"name": "Unknown User", "real_name": "Unknown User", "display_name": "Unknown User"}}
#         user_cache[user_id] = user_data
#         return user_data

# def find_channel(client, channel_input):
#     logger.info(f"Attempting to find channel: {{channel_input}}")
    
#     if not channel_input:
#         logger.error("Channel input is empty")
#         return None
    
#     # If it's already a valid channel ID (starts with C and is 11 characters long), use it directly
#     if channel_input.startswith('C') and len(channel_input) == 11:
#         logger.info(f"Using provided channel ID directly: {{channel_input}}")
#         return channel_input
    
#     # Remove '#' if present
#     channel_input = channel_input.lstrip('#')
    
#     # Try to find the channel by name
#     try:
#         for response in client.conversations_list(types="public_channel,private_channel"):
#             for channel in response["channels"]:
#                 # Try exact match first
#                 if channel["name"].lower() == channel_input.lower():
#                     logger.info(f"Exact match found: {{channel['id']}}")
#                     return channel["id"]
#                 # Fall back to fuzzy match if no exact match found
#                 elif fuzz.ratio(channel["name"].lower(), channel_input.lower()) > 80:
#                     logger.info(f"Close match found: {{channel['name']}} (ID: {{channel['id']}})")
#                     return channel["id"]
#     except SlackApiError as e:
#         logger.error(f"Error listing channels: {{e}}")

#     logger.error(f"Channel not found: {{channel_input}}")
#     return None

# def process_time_filter(oldest_param):
#     if not oldest_param:
#         return None
        
#     # Handle direct Unix timestamp
#     if oldest_param.replace('.', '').isdigit():
#         return oldest_param
        
#     time_pattern = re.match(r'(\d+)([hdmw])', oldest_param.lower())
#     if time_pattern:
#         amount = int(time_pattern.group(1))
#         unit = time_pattern.group(2)
        
#         # Calculate seconds based on unit
#         if unit == 'h':
#             seconds = 3600 * amount
#         elif unit == 'd':
#             seconds = 86400 * amount
#         elif unit == 'w':
#             seconds = 604800 * amount
#         elif unit == 'm':
#             seconds = 60 * amount
#         else:
#             return None
            
#         # Get current time
#         current_time = time()
#         target_time = current_time - seconds
        
#         # Format with 6 decimal places
#         return f"{{target_time:.6f}}"
    
#     return None

# def retry_with_backoff(func, max_retries=5, initial_delay=2, max_delay=60):
#     retries = 0
#     delay = initial_delay
    
#     while retries < max_retries:
#         try:
#             return func()
#         except SlackApiError as e:
#             error_message = str(e)
            
#             # Check if rate limited
#             if "ratelimited" in error_message:
#                 # Add jitter to avoid thundering herd problem
#                 jitter = random.uniform(0, 0.1 * delay)
#                 sleep_time = delay + jitter
                
#                 logger.warning(f"Rate limited. Retrying in {{sleep_time:.2f}} seconds (attempt {{retries+1}}/{{max_retries}})")
#                 sleep(sleep_time)
                
#                 # Exponential backoff
#                 delay = min(delay * 2, max_delay)
#                 retries += 1
#             else:
#                 # If not rate limited, re-raise the exception
#                 raise
    
#     # If we've exhausted retries, raise the last exception
#     raise Exception(f"Failed after {{max_retries}} retries due to rate limiting")

# def get_channel_messages(client, channel_id, oldest):
#     try:
#         messages = []
#         cursor = None
#         latest = None  # For time-based pagination
        
#         # Use pagination to get all messages
#         while True:
#             params = {{
#                 "channel": channel_id,
#                 "oldest": oldest,
#                 "limit": 250  # Recommended by Slack API
#             }}
            
#             # Add cursor for pagination if we have one
#             if cursor:
#                 params["cursor"] = cursor
            
#             # Add latest timestamp for time-based pagination if we have one
#             if latest:
#                 params["latest"] = latest
            
#             # Use retry with backoff for API call
#             def api_call():
#                 return client.conversations_history(**params)
                
#             response = retry_with_backoff(api_call)
#             batch = response["messages"]
            
#             if not batch:
#                 logger.info("No messages returned in this batch")
#                 break
                
#             messages.extend(batch)
            
#             # Check if there are more messages to fetch via cursor
#             if response.get("has_more", False) and response.get("response_metadata", {{}}).get("next_cursor"):
#                 cursor = response.get("response_metadata", {{}}).get("next_cursor")
#                 latest = None  # Reset latest when using cursor
#             # If has_more is true but no cursor, use time-based pagination
#             elif response.get("has_more", False):
#                 # Get the timestamp of the oldest message in this batch
#                 if batch:
#                     latest = batch[-1].get("ts")
#                     cursor = None  # Reset cursor when using time-based pagination
#                 else:
#                     break
#             else:
#                 break
                
#             # Safety limit to prevent excessive API calls
#             if len(messages) >= 50000:
#                 logger.info(f"Reached maximum message limit (50000), stopping pagination")
#                 break
        
#         logger.info(f"Total messages retrieved: {{len(messages)}}")
        
#         # Process messages for OOO analysis
#         processed_messages = []
        
#         for msg in messages:
#             # Get user information
#             user_id = msg.get("user", "")
#             user_info = get_user_info(client, user_id)
            
#             # Convert timestamp to readable date
#             message_ts = msg.get("ts", "")
#             message_date = "Unknown Date"
#             if message_ts:
#                 try:
#                     message_datetime = datetime.fromtimestamp(float(message_ts))
#                     message_date = message_datetime.strftime("%Y-%m-%d")
#                 except (ValueError, TypeError):
#                     logger.warning(f"Could not parse timestamp: {{message_ts}}")
            
#             processed_msg = {{
#                 "message": msg.get("text", ""),
#                 "timestamp": message_ts,
#                 "user_id": user_id,
#                 "user_name": user_info["display_name"],
#                 "message_date": message_date
#             }}

#             # Check if message has a thread and get replies
#             thread_ts = msg.get("thread_ts")
#             if thread_ts and thread_ts == msg.get("ts"):
#                 replies = get_thread_replies(client, channel_id, thread_ts)
                
#                 # Process each reply as a separate message for OOO analysis
#                 for reply in replies:
#                     reply_user_id = reply.get("user", "")
#                     reply_user_info = get_user_info(client, reply_user_id)
                    
#                     # Convert reply timestamp to readable date
#                     reply_ts = reply.get("ts", "")
#                     reply_date = "Unknown Date"
#                     if reply_ts:
#                         try:
#                             reply_datetime = datetime.fromtimestamp(float(reply_ts))
#                             reply_date = reply_datetime.strftime("%Y-%m-%d")
#                         except (ValueError, TypeError):
#                             logger.warning(f"Could not parse reply timestamp: {{reply_ts}}")
                    
#                     processed_messages.append({{
#                         "message": reply.get("text", ""),
#                         "timestamp": reply_ts,
#                         "user_id": reply_user_id,
#                         "user_name": reply_user_info["display_name"],
#                         "message_date": reply_date
#                     }})

#             processed_messages.append(processed_msg)
            
#         return processed_messages
        
#     except SlackApiError as e:
#         logger.error(f"Error fetching channel history: {{e}}")
#         return []

# def get_thread_replies(client, channel_id, thread_ts):
#     try:
#         replies = []
#         cursor = None
#         while True:
#             params = {{
#                 "channel": channel_id,
#                 "ts": thread_ts,
#                 "limit": 200
#             }}
#             if cursor:
#                 params["cursor"] = cursor
            
#             # Use retry with backoff for API call
#             def api_call():
#                 return client.conversations_replies(**params)
                
#             response = retry_with_backoff(api_call)
#             thread_messages = response["messages"]
            
#             # Skip the first message (it's the parent)
#             replies_batch = thread_messages[1:] if len(thread_messages) > 1 else []
#             replies.extend(replies_batch)
            
#             if response.get("has_more", False) and response.get("response_metadata", {{}}).get("next_cursor"):
#                 cursor = response.get("response_metadata", {{}}).get("next_cursor")
#             else:
#                 break
        
#         return replies

#     except Exception as e:
#         logger.error(f"Error fetching replies for thread {{thread_ts}}: {{e}}")
#         return []

# def analyze_message_for_ooo(message_data):
#     \"\"\"Analyze a single message for OOO declarations using LLM\"\"\"
#     try:
#         prompt = f\"\"\"You are an expert assistant for extracting out-of-office (OOO) information from Slack messages.

# Given a message, the user's name, the date they posted it (date_message_was_sent), and today's date (today_date), identify whether the user is indicating they will be out of office. If they are, return a list of the specific date(s) they are expected to be out.

# Always resolve relative dates (like "tomorrow" or "next Friday") based on date_message_was_sent. Assume users are in the same year unless otherwise stated.

# Respond ONLY with valid JSON in this exact format (no additional text):
# {{
#   "is_ooo_message": true/false,
#   "declared_ooo_date": ["YYYY-MM-DD", "YYYY-MM-DD"],
#   "reason": "Brief explanation of why this is/isn't an OOO message",
#   "confidence": "high/medium/low"
# }}

# ### Input:
# User: {{message_data['user_name']}}
# Date message was sent: {{message_data['message_date']}}
# Today's date: {{datetime.now().strftime("%Y-%m-%d")}}
# Message: "{{message_data['message']}}"
# \"\"\"

#         llm_messages = [
#             {{"role": "system", "content": "You are a specialized assistant for extracting out-of-office information from Slack messages. Always respond with valid JSON only."}},
#             {{"role": "user", "content": prompt}}
#         ]

#         base_url = os.environ.get("LLM_BASE_URL")

#         response = litellm.completion(
#             messages=llm_messages,
#             model="openai/Llama-4-Scout",
#             api_key=os.environ.get("LLM_API_KEY"),
#             base_url=base_url,
#             stream=False,
#             user=os.environ.get("KUBIYA_USER_EMAIL"),
#             max_tokens=512,
#             temperature=0.1,
#             top_p=0.1,
#             presence_penalty=0.0,
#             frequency_penalty=0.0,
#             timeout=15,
#         )

#         result_text = response.choices[0].message.content.strip()
        
#         # Parse the JSON response
#         try:
#             result = json.loads(result_text)
#             return result
#         except json.JSONDecodeError as e:
#             logger.warning(f"Failed to parse LLM JSON response: {{result_text}}. Error: {{e}}")
#             return {{
#                 "is_ooo_message": False,
#                 "declared_ooo_date": [],
#                 "reason": "Failed to parse LLM response",
#                 "confidence": "low"
#             }}

#     except Exception as e:
#         logger.error(f"Error analyzing message for OOO: {{str(e)}}")
#         return {{
#             "is_ooo_message": False,
#             "declared_ooo_date": [],
#             "reason": f"Error during analysis: {{str(e)}}",
#             "confidence": "low"
#         }}

# def execute_slack_action(token, action, operation, **kwargs):
#     # Print current date and time at the beginning
#     current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#     today_date = datetime.now().strftime("%Y-%m-%d")
#     logger.info(f"Starting Slack OOO analysis at: {{current_datetime}}")
#     print(f"Current date and time: {{current_datetime}}")
    
#     client = WebClient(token=token)
#     logger.info(f"Executing Slack OOO analysis with params: {{kwargs}}")
    
#     channel = kwargs.get('channel')
#     oldest = kwargs.get('oldest', '24h')  # Default to last 24 hours
    
#     if not channel:
#         return {{"success": False, "error": "Channel parameter is required"}}
    
#     channel_id = find_channel(client, channel)
#     if not channel_id:
#         return {{"success": False, "error": f"Channel not found: {{channel}}"}}
    
#     # Process time filter
#     oldest_ts = process_time_filter(oldest)
#     if not oldest_ts:
#         return {{"success": False, "error": "Invalid time filter format. Use format like '1h', '2d', '1w', or '30m'"}}
    
#     logger.info(f"Fetching messages from channel {{channel_id}} since {{oldest_ts}}")
    
#     # Get messages
#     messages = get_channel_messages(client, channel_id, oldest_ts)
    
#     if not messages:
#         return {{
#             "success": True,
#             "today": today_date,
#             "ooo_declarations": [],
#             "message": "No messages found in the specified time period"
#         }}
    
#     logger.info(f"Found {{len(messages)}} messages to analyze for OOO declarations")
    
#     # Analyze each message for OOO content
#     ooo_declarations = []
#     seen_declarations = set()  # For deduplication: (user_name, date)
    
#     for i, message_data in enumerate(messages):
#         if not message_data.get('message', '').strip():
#             continue  # Skip empty messages
            
#         logger.info(f"Analyzing message {{i+1}}/{{len(messages)}} from {{message_data.get('user_name', 'Unknown')}}")
        
#         analysis_result = analyze_message_for_ooo(message_data)
        
#         if analysis_result.get('is_ooo_message', False):
#             # Create OOO declaration entry
#             for ooo_date in analysis_result.get('declared_ooo_date', []):
#                 # Check for duplicates
#                 dedup_key = (message_data['user_name'], ooo_date)
#                 if dedup_key not in seen_declarations:
#                     seen_declarations.add(dedup_key)
                    
#                     ooo_entry = {{
#                         "user_name": message_data['user_name'],
#                         "declared_ooo_date": [ooo_date] if isinstance(ooo_date, str) else ooo_date,
#                         "date_message_was_sent": message_data['message_date'],
#                         "raw_message": message_data['message']
#                     }}
#                     ooo_declarations.append(ooo_entry)
#                     logger.info(f"Found OOO declaration: {{message_data['user_name']}} on {{ooo_date}}")
    
#     # Group by user and combine date ranges where possible
#     user_declarations = {{}}
#     for declaration in ooo_declarations:
#         user = declaration['user_name']
#         if user not in user_declarations:
#             user_declarations[user] = []
#         user_declarations[user].append(declaration)
    
#     # Merge declarations for the same message
#     final_declarations = []
#     for user, declarations in user_declarations.items():
#         # Group by message date and raw message
#         message_groups = {{}}
#         for decl in declarations:
#             key = (decl['date_message_was_sent'], decl['raw_message'])
#             if key not in message_groups:
#                 message_groups[key] = {{
#                     "user_name": decl['user_name'],
#                     "declared_ooo_date": [],
#                     "date_message_was_sent": decl['date_message_was_sent'],
#                     "raw_message": decl['raw_message']
#                 }}
#             message_groups[key]['declared_ooo_date'].extend(decl['declared_ooo_date'])
        
#         # Remove duplicates from date lists
#         for group in message_groups.values():
#             group['declared_ooo_date'] = sorted(list(set(group['declared_ooo_date'])))
#             final_declarations.append(group)
    
#     # Sort by date message was sent
#     final_declarations.sort(key=lambda x: x['date_message_was_sent'])
    
#     logger.info(f"Analysis complete. Found {{len(final_declarations)}} OOO declarations")
    
#     return {{
#         "success": True,
#         "today": today_date,
#         "ooo_declarations": final_declarations
#     }}

# if __name__ == "__main__":
#     token = os.environ.get("SLACK_API_TOKEN")
#     if not token:
#         logger.error("SLACK_API_TOKEN is not set")
#         print(json.dumps({{"success": False, "error": "SLACK_API_TOKEN is not set"}}))
#         sys.exit(1)

#     logger.info("Starting Slack OOO analysis...")
#     arg_names = {arg_names_json}
#     args = {{}}
#     for arg in arg_names:
#         if arg in os.environ:
#             args[arg] = os.environ[arg]
    
#     result = execute_slack_action(token, "{action}", "{name}", **args)
#     logger.info("Slack OOO analysis completed")
#     print(json.dumps(result))
# """
        
#         super().__init__(
#             name=name,
#             description=description,
#             icon_url=SLACK_ICON_URL,
#             type="docker",
#             image="python:3.11-slim",
#             content="pip install -q slack-sdk fuzzywuzzy python-Levenshtein litellm tenacity > /dev/null 2>&1 && python /tmp/script.py",
#             args=args,
#             env=env,
#             secrets=secrets,
#             long_running=long_running,
#             mermaid=mermaid_diagram,
#             with_files=[
#                 FileSpec(
#                     destination="/tmp/script.py",
#                     content=script_content,
#                 )
#             ],
#         )

class SlackOutOfOfficeTool(Tool):
    def __init__(self, name, description, action, args, env=[], long_running=False, mermaid_diagram=None):
        env = ["KUBIYA_USER_EMAIL", "LLM_BASE_URL", *env]
        secrets = ["SLACK_API_TOKEN", "LLM_API_KEY"]
        
        arg_names_json = json.dumps([arg.name for arg in args])
        
        go_script_content = f"""package main

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"regexp"
	"sort"
	"strconv"
	"strings"
	"sync"
	"time"

	"github.com/slack-go/slack"
)

type UserInfo struct {{
	Name        string `json:"name"`
	RealName    string `json:"real_name"`
	DisplayName string `json:"display_name"`
}}

type MessageData struct {{
	Message     string `json:"message"`
	Timestamp   string `json:"timestamp"`
	UserID      string `json:"user_id"`
	UserName    string `json:"user_name"`
	MessageDate string `json:"message_date"`
}}

type OOOAnalysis struct {{
	IsOOOMessage      bool     `json:"is_ooo_message"`
	DeclaredOOODate   []string `json:"declared_ooo_date"`
	Reason            string   `json:"reason"`
	Confidence        string   `json:"confidence"`
}}

type OOODeclaration struct {{
	UserName            string   `json:"user_name"`
	DeclaredOOODate     []string `json:"declared_ooo_date"`
	DateMessageWasSent  string   `json:"date_message_was_sent"`
	RawMessage          string   `json:"raw_message"`
}}

type OOOResult struct {{
	Success         bool              `json:"success"`
	Today           string            `json:"today"`
	OOODeclarations []OOODeclaration  `json:"ooo_declarations"`
	Error           string            `json:"error,omitempty"`
}}

type LLMRequest struct {{
	Messages    []LLMMessage `json:"messages"`
	Model       string       `json:"model"`
	MaxTokens   int          `json:"max_tokens"`
	Temperature float64      `json:"temperature"`
	TopP        float64      `json:"top_p"`
	User        string       `json:"user"`
	Stream      bool         `json:"stream"`
}}

type LLMMessage struct {{
	Role    string `json:"role"`
	Content string `json:"content"`
}}

type LLMResponse struct {{
	Choices []struct {{
		Message struct {{
			Content string `json:"content"`
		}} `json:"message"`
	}} `json:"choices"`
}}

var (
	userCache      = make(map[string]UserInfo)
	userCacheMutex = sync.RWMutex{{}}
	httpClient     = &http.Client{{Timeout: 30 * time.Second}}
)

func main() {{
	token := os.Getenv("SLACK_API_TOKEN")
	if token == "" {{
		result := OOOResult{{Success: false, Error: "SLACK_API_TOKEN is not set"}}
		output, _ := json.Marshal(result)
		fmt.Println(string(output))
		os.Exit(1)
	}}

	argNames := {arg_names_json}
	args := make(map[string]string)
	for _, arg := range argNames {{
		if val := os.Getenv(arg); val != "" {{
			args[arg] = val
		}}
	}}

	result := executeSlackAction(token, args)
	output, _ := json.Marshal(result)
	fmt.Println(string(output))
}}

func executeSlackAction(token string, args map[string]string) OOOResult {{
	currentTime := time.Now()
	today := currentTime.Format("2006-01-02")
	
	log.Printf("Starting Slack OOO analysis at: %s", currentTime.Format("2006-01-02 15:04:05"))
	fmt.Printf("Current date and time: %s\\n", currentTime.Format("2006-01-02 15:04:05"))

	api := slack.New(token)
	
	channel := args["channel"]
	if channel == "" {{
		return OOOResult{{Success: false, Error: "Channel parameter is required"}}
	}}

	oldest := args["oldest"]
	if oldest == "" {{
		oldest = "24h"
	}}

	channelID, err := findChannel(api, channel)
	if err != nil {{
		return OOOResult{{Success: false, Error: fmt.Sprintf("Channel not found: %s", channel)}}
	}}

	oldestTimestamp, err := processTimeFilter(oldest)
	if err != nil {{
		return OOOResult{{Success: false, Error: fmt.Sprintf("Invalid time filter: %s", err)}}
	}}

	log.Printf("Fetching messages from channel %s since %s", channelID, oldestTimestamp)

	messages, err := getChannelMessages(api, channelID, oldestTimestamp)
	if err != nil {{
		return OOOResult{{Success: false, Error: fmt.Sprintf("Error fetching messages: %s", err)}}
	}}

	if len(messages) == 0 {{
		return OOOResult{{
			Success:         true,
			Today:           today,
			OOODeclarations: []OOODeclaration{{}},
		}}
	}}

	log.Printf("Found %d messages to analyze for OOO declarations", len(messages))

	declarations := analyzeMessagesForOOO(messages, today)

	log.Printf("Analysis complete. Found %d OOO declarations", len(declarations))

	return OOOResult{{
		Success:         true,
		Today:           today,
		OOODeclarations: declarations,
	}}
}}

func findChannel(api *slack.Client, channelInput string) (string, error) {{
	log.Printf("Attempting to find channel: %s", channelInput)

	if channelInput == "" {{
		return "", fmt.Errorf("channel input is empty")
	}}

	if strings.HasPrefix(channelInput, "C") && len(channelInput) == 11 {{
		log.Printf("Using provided channel ID directly: %s", channelInput)
		return channelInput, nil
	}}

	channelInput = strings.TrimPrefix(channelInput, "#")

	channels, _, err := api.GetConversations(&slack.GetConversationsParameters{{
		Types: []string{{"public_channel", "private_channel"}},
	}})
	if err != nil {{
		return "", err
	}}

	for _, channel := range channels {{
		if strings.EqualFold(channel.Name, channelInput) {{
			log.Printf("Exact match found: %s", channel.ID)
			return channel.ID, nil
		}}
	}}

	return "", fmt.Errorf("channel not found: %s", channelInput)
}}

func processTimeFilter(oldestParam string) (string, error) {{
	if oldestParam == "" {{
		return "", fmt.Errorf("oldest parameter is empty")
	}}

	if matched, _ := regexp.MatchString(`^\\d+(\\.\\d+)?$`, oldestParam); matched {{
		return oldestParam, nil
	}}

	re := regexp.MustCompile(`^(\\d+)([hdmw])$`)
	matches := re.FindStringSubmatch(strings.ToLower(oldestParam))
	if len(matches) != 3 {{
		return "", fmt.Errorf("invalid time format")
	}}

	amount, _ := strconv.Atoi(matches[1])
	unit := matches[2]

	var seconds int
	switch unit {{
	case "h":
		seconds = 3600 * amount
	case "d":
		seconds = 86400 * amount
	case "w":
		seconds = 604800 * amount
	case "m":
		seconds = 60 * amount
	default:
		return "", fmt.Errorf("unsupported time unit")
	}}

	targetTime := time.Now().Unix() - int64(seconds)
	return fmt.Sprintf("%.6f", float64(targetTime)), nil
}}

func getUserInfo(api *slack.Client, userID string) UserInfo {{
	if userID == "" {{
		return UserInfo{{Name: "Unknown User", RealName: "Unknown User", DisplayName: "Unknown User"}}
	}}

	userCacheMutex.RLock()
	if cached, exists := userCache[userID]; exists {{
		userCacheMutex.RUnlock()
		return cached
	}}
	userCacheMutex.RUnlock()

	user, err := api.GetUserInfo(userID)
	if err != nil {{
		log.Printf("Could not retrieve user info for %s: %s", userID, err)
		userInfo := UserInfo{{Name: "Unknown User", RealName: "Unknown User", DisplayName: "Unknown User"}}
		
		userCacheMutex.Lock()
		userCache[userID] = userInfo
		userCacheMutex.Unlock()
		
		return userInfo
	}}

	displayName := user.Profile.DisplayName
	if displayName == "" {{
		displayName = user.RealName
		if displayName == "" {{
			displayName = user.Name
		}}
	}}

	userInfo := UserInfo{{
		Name:        user.Name,
		RealName:    user.RealName,
		DisplayName: displayName,
	}}

	userCacheMutex.Lock()
	userCache[userID] = userInfo
	userCacheMutex.Unlock()

	return userInfo
}}

func getChannelMessages(api *slack.Client, channelID, oldest string) ([]MessageData, error) {{
	var allMessages []MessageData
	var cursor string

	for {{
		params := &slack.GetConversationHistoryParameters{{
			ChannelID: channelID,
			Oldest:    oldest,
			Limit:     200,
			Cursor:    cursor,
		}}

		history, err := api.GetConversationHistory(params)
		if err != nil {{
			return nil, err
		}}

		if len(history.Messages) == 0 {{
			break
		}}

		messageChan := make(chan MessageData, len(history.Messages)*2)
		var wg sync.WaitGroup

		for _, msg := range history.Messages {{
			wg.Add(1)
			go func(m slack.Message) {{
				defer wg.Done()
				
				userInfo := getUserInfo(api, m.User)
				
				messageDate := "Unknown Date"
				if m.Timestamp != "" {{
					if ts, err := strconv.ParseFloat(m.Timestamp, 64); err == nil {{
						messageDate = time.Unix(int64(ts), 0).Format("2006-01-02")
					}}
				}}

				processedMsg := MessageData{{
					Message:     m.Text,
					Timestamp:   m.Timestamp,
					UserID:      m.User,
					UserName:    userInfo.DisplayName,
					MessageDate: messageDate,
				}}

				messageChan <- processedMsg

				if m.ThreadTimestamp != "" && m.ThreadTimestamp == m.Timestamp {{
					replies, _, _, err := api.GetConversationReplies(&slack.GetConversationRepliesParameters{{
						ChannelID: channelID,
						Timestamp: m.ThreadTimestamp,
					}})
					if err == nil && len(replies) > 1 {{
						for _, reply := range replies[1:] {{
							replyUserInfo := getUserInfo(api, reply.User)
							replyDate := "Unknown Date"
							if reply.Timestamp != "" {{
								if ts, err := strconv.ParseFloat(reply.Timestamp, 64); err == nil {{
									replyDate = time.Unix(int64(ts), 0).Format("2006-01-02")
								}}
							}}

							replyMsg := MessageData{{
								Message:     reply.Text,
								Timestamp:   reply.Timestamp,
								UserID:      reply.User,
								UserName:    replyUserInfo.DisplayName,
								MessageDate: replyDate,
							}}

							messageChan <- replyMsg
						}}
					}}
				}}
			}}(msg)
		}}

		go func() {{
			wg.Wait()
			close(messageChan)
		}}()

		for msg := range messageChan {{
			allMessages = append(allMessages, msg)
		}}

		if !history.HasMore {{
			break
		}}
		cursor = history.ResponseMetaData.NextCursor
	}}

	log.Printf("Total messages retrieved: %d", len(allMessages))
	return allMessages, nil
}}

func analyzeMessagesForOOO(messages []MessageData, today string) []OOODeclaration {{
	const maxConcurrency = 10
	semaphore := make(chan struct{{}}, maxConcurrency)
	resultChan := make(chan *OOODeclaration, len(messages))
	var wg sync.WaitGroup

	for i, message := range messages {{
		if strings.TrimSpace(message.Message) == "" {{
			continue
		}}

		wg.Add(1)
		go func(msg MessageData, index int) {{
			defer wg.Done()
			
			semaphore <- struct{{}}{{}}
			defer func() {{ <-semaphore }}()

			log.Printf("Analyzing message %d/%d from %s", index+1, len(messages), msg.UserName)
			
			analysis := analyzeMessageForOOO(msg, today)
			if analysis.IsOOOMessage && len(analysis.DeclaredOOODate) > 0 {{
				declaration := &OOODeclaration{{
					UserName:           msg.UserName,
					DeclaredOOODate:    analysis.DeclaredOOODate,
					DateMessageWasSent: msg.MessageDate,
					RawMessage:         msg.Message,
				}}
				resultChan <- declaration
			}}
		}}(message, i)
	}}

	go func() {{
		wg.Wait()
		close(resultChan)
	}}()

	declarationMap := make(map[string]*OOODeclaration)
	
	for declaration := range resultChan {{
		key := fmt.Sprintf("%s_%s_%s", declaration.UserName, declaration.DateMessageWasSent, declaration.RawMessage)
		if existing, exists := declarationMap[key]; exists {{
			dateSet := make(map[string]bool)
			for _, date := range existing.DeclaredOOODate {{
				dateSet[date] = true
			}}
			for _, date := range declaration.DeclaredOOODate {{
				dateSet[date] = true
			}}
			
			var mergedDates []string
			for date := range dateSet {{
				mergedDates = append(mergedDates, date)
			}}
			sort.Strings(mergedDates)
			existing.DeclaredOOODate = mergedDates
		}} else {{
			declarationMap[key] = declaration
		}}
	}}

	var finalDeclarations []OOODeclaration
	for _, declaration := range declarationMap {{
		finalDeclarations = append(finalDeclarations, *declaration)
	}}

	sort.Slice(finalDeclarations, func(i, j int) bool {{
		return finalDeclarations[i].DateMessageWasSent < finalDeclarations[j].DateMessageWasSent
	}})

	return finalDeclarations
}}

func analyzeMessageForOOO(messageData MessageData, today string) OOOAnalysis {{
	prompt := fmt.Sprintf(`You are an expert assistant for extracting out-of-office (OOO) information from Slack messages.

Given a message, the user's name, the date they posted it (date_message_was_sent), and today's date (today_date), identify whether the user is indicating they will be out of office. If they are, return a list of the specific date(s) they are expected to be out.

Always resolve relative dates (like "tomorrow" or "next Friday") based on date_message_was_sent. Assume users are in the same year unless otherwise stated.

Respond ONLY with valid JSON in this exact format (no additional text):
{{
  "is_ooo_message": true,
  "declared_ooo_date": ["2025-01-25", "2025-01-26"],
  "reason": "Brief explanation of why this is/isn't an OOO message",
  "confidence": "high"
}}

### Input:
User: %s
Date message was sent: %s
Today's date: %s
Message: "%s"`, messageData.UserName, messageData.MessageDate, today, messageData.Message)

	llmRequest := LLMRequest{{
		Messages: []LLMMessage{{
			{{Role: "system", Content: "You are a specialized assistant for extracting out-of-office information from Slack messages. Always respond with valid JSON only."}},
			{{Role: "user", Content: prompt}},
		}},
		Model:       "openai/Llama-4-Scout",
		MaxTokens:   512,
		Temperature: 0.1,
		TopP:        0.1,
		User:        os.Getenv("KUBIYA_USER_EMAIL"),
		Stream:      false,
	}}

	jsonData, err := json.Marshal(llmRequest)
	if err != nil {{
		return OOOAnalysis{{IsOOOMessage: false, Reason: "Error marshaling request", Confidence: "low"}}
	}}

	baseURL := os.Getenv("LLM_BASE_URL")
	apiKey := os.Getenv("LLM_API_KEY")

	req, err := http.NewRequest("POST", baseURL+"/v1/chat/completions", bytes.NewBuffer(jsonData))
	if err != nil {{
		return OOOAnalysis{{IsOOOMessage: false, Reason: "Error creating request", Confidence: "low"}}
	}}

	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer "+apiKey)

	resp, err := httpClient.Do(req)
	if err != nil {{
		return OOOAnalysis{{IsOOOMessage: false, Reason: "Error making request", Confidence: "low"}}
	}}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {{
		return OOOAnalysis{{IsOOOMessage: false, Reason: "Error reading response", Confidence: "low"}}
	}}

	var llmResponse LLMResponse
	if err := json.Unmarshal(body, &llmResponse); err != nil {{
		return OOOAnalysis{{IsOOOMessage: false, Reason: "Error parsing LLM response", Confidence: "low"}}
	}}

	if len(llmResponse.Choices) == 0 {{
		return OOOAnalysis{{IsOOOMessage: false, Reason: "No choices in LLM response", Confidence: "low"}}
	}}

	content := strings.TrimSpace(llmResponse.Choices[0].Message.Content)
	
	var analysis OOOAnalysis
	if err := json.Unmarshal([]byte(content), &analysis); err != nil {{
		return OOOAnalysis{{IsOOOMessage: false, Reason: "Failed to parse LLM response", Confidence: "low"}}
	}}

	return analysis
}}
"""

        go_mod_content = """module slack-ooo-analyzer

go 1.21

require github.com/slack-go/slack v0.12.3

require github.com/gorilla/websocket v1.4.2 // indirect
"""

        super().__init__(
            name=name,
            description=description,
            icon_url=SLACK_ICON_URL,
            type="docker",
            image="golang:1.21-alpine",
            content="cd /tmp && go mod tidy && go run main.go",
            args=args,
            env=env,
            secrets=secrets,
            long_running=long_running,
            mermaid=mermaid_diagram,
            with_files=[
                FileSpec(
                    destination="/tmp/go.mod",
                    content=go_mod_content,
                ),
                FileSpec(
                    destination="/tmp/main.go",
                    content=go_script_content,
                )
            ],
        )