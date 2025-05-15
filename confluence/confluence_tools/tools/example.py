from kubiya_sdk.tools.models import Tool, Arg, FileSpec
import json

SLACK_ICON_URL = "https://a.slack-edge.com/80588/marketing/img/icons/icon_slack_hash_colored.png"


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
            processed_msg = {{
                "message": msg.get("text", ""),
                "timestamp": msg.get("ts", "")
            }}

            # Check if message has a thread
            thread_ts = msg.get("thread_ts")
            if thread_ts and thread_ts == msg.get("ts"):
                replies = get_thread_replies(client, channel_id, thread_ts)
                
                # Attach replies under parent message
                processed_msg["replies"] = [
                    {{
                        "message": reply.get("text", ""),
                        "timestamp": reply.get("ts", "")
                    }}
                    for reply in replies
                ]
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
                # Include a unique message ID and make the link more prominent
                lines.append(f"[MSG_ID:{{i+1}}] {{msg['message']}}\\nLINK: {{message_link}}\\nTIMESTAMP: {{msg['timestamp']}}\\n")
                
                for j, reply in enumerate(msg.get("replies", [])):
                    # Create a reply link using thread timestamp and reply timestamp
                    reply_link = f"https://slack.com/archives/{{channel_id}}/p{{msg['timestamp'].replace('.', '')}}?thread_ts={{msg['timestamp']}}&cid={{channel_id}}"
                    # Include a unique reply ID and make the link more prominent
                    lines.append(f"  [REPLY_ID:{{i+1}}.{{j+1}}] {{reply['message']}}\\n  LINK: {{reply_link}}\\n  TIMESTAMP: {{reply['timestamp']}}\\n")
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