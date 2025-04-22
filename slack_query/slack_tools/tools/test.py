import os
import sys
import json
import logging
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import litellm
from time import time
import re
from fuzzywuzzy import fuzz

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
        
    time_pattern = re.match(r'(\d+)([hdm])', oldest_param.lower())
    if time_pattern:
        amount = int(time_pattern.group(1))
        unit = time_pattern.group(2)
        seconds = {{'h': 3600, 'd': 86400, 'm': 60}}[unit]
        current_time = time()
        offset = amount * seconds
        target_time = current_time - offset
        return f"{{target_time:.6f}}"  # Format with exactly 6 decimal places
    return None

def process_slack_messages(messages, is_reply=False):
    logger.info(f"Processing {{len(messages)}} messages")
    
    # Print each message individually instead of joining
    for msg in messages:
        processed_msg = {{
            "message": msg.get("text", ""),
            "timestamp": msg.get("ts", ""),
            "reply_count": msg.get("reply_count", 0)
        }}
        
        # Only include reply_count for main messages, not for replies
        if not is_reply:
            processed_msg["reply_count"] = msg.get("reply_count", 0)
            
        print(json.dumps(processed_msg))  # Print each message directly
    
    return "Messages printed individually"  # Return a placeholder

def get_channel_messages(client, channel_id, oldest):
    try:
        params = {{
            "channel": channel_id,
            "oldest": oldest
        }}
            
        response = client.conversations_history(**params)
        messages = response["messages"]
        
        # Process messages using the same format as SlackTool
        processed_messages = []
        for msg in messages:
            processed_msg = {{
                "message": msg.get("text", ""),
                "timestamp": msg.get("ts", ""),
                "reply_count": msg.get("reply_count", 0)
            }}
            processed_messages.append(processed_msg)
        
        logger.info(f"Retrieved {{len(processed_messages)}} messages from channel")
        logger.info(f"Message sample: {{processed_messages[:2]}}")  # Log first two messages for debugging
        return processed_messages
        
    except SlackApiError as e:
        logger.error(f"Error fetching channel history: {{e}}")
        return []

def analyze_messages_with_llm(messages, query):
    try:
        logger.info(f"Analyzing {len(messages)} messages with query: {query}")
        
        messages_text = "\\n".join([
            f"Message {i+1} (ts: {msg['timestamp']}, replies: {msg['reply_count']}): {msg['message']}" 
            for i, msg in enumerate(messages)
        ])
        
        logger.info("Constructed messages text for analysis")
        
        prompt = (
            "Based on these Slack messages, answer the following query. "
            "If you can't find a clear answer, say so.\\n\\n"
            f"Query: {query}\\n\\n"
            f"Messages:\\n{messages_text}"
        )
        
        logger.info("Sending request to LLM")

        # Configure litellm
        litellm.set_verbose = True
        litellm.request_timeout = 15  # Set shorter timeout
        litellm.num_retries = 2  # Limit retries
        
        messages = [
            {"role": "system", "content": "You are a helpful assistant that provides clear, direct answers based on Slack message content."},
            {"role": "user", "content": prompt}
        ]

        modified_metadata = {
            "user_id": os.environ.get("KUBIYA_USER_EMAIL", "unknown-user")
        }
        
        # Get the base URL and ensure it ends with a trailing slash
        base_url = os.environ.get("LITELLM_API_BASE", "")
        if base_url and not base_url.endswith('/'):
            base_url = base_url + '/'
        
        response = litellm.completion(
            messages=messages,
            model="openai/Llama-4-Scout",
            api_key=os.environ.get("LITELLM_API_KEY"),
            base_url=base_url,  # Use the corrected base URL
            stream=False,
            user="michael.bauer@kubiya.ai-staging",
            max_tokens=2048,
            temperature=0.7,
            top_p=0.1,
            presence_penalty=0.0,
            frequency_penalty=0.0,
            timeout=30,  # Increased timeout from 15 to 30 seconds
            extra_body={
                "metadata": modified_metadata
            }
        )
        
        answer = response.choices[0].message.content.strip()
        logger.info(f"Received response from LLM: {{answer[:100]}}...")
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
        return {{"success": False, "answer": "Invalid time filter format. Use format like '1h', '2d', or '30m'"}}
    
    logger.info(f"Fetching messages from channel {{channel_id}} since {{oldest_ts}}")
    
    # Get messages
    messages = get_channel_messages(client, channel_id, oldest_ts)
    
    if not messages:
        return {{"success": True, "answer": "No messages found in the specified time period"}}
    
    logger.info(f"Found {{len(messages)}} messages to analyze")
    
    # Get answer from LLM
    answer = analyze_messages_with_llm(messages, query)
    
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