#!/usr/bin/env python
import os
import sys
import json
import logging
from pathlib import Path

# Handle imports gracefully during discovery phase
try:
    from slack_sdk import WebClient
    from slack_sdk.errors import SlackApiError
    from fuzzywuzzy import fuzz
except ImportError:
    print("⚠️  Import Warning:")
    print("   Could not import slack_sdk or fuzzywuzzy.")
    print("   This is expected during discovery phase and can be safely ignored.")
    print("   The required modules will be available during actual execution.")
    pass

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def find_channel(client, channel_input):
    # If it's already a valid channel ID (starts with C and is 11 characters long), use it directly
    if channel_input.startswith("C") and len(channel_input) == 11:
        return channel_input
    
    # Remove '#' if present
    channel_input = channel_input.lstrip("#")
    
    # Try to find the channel by name
    try:
        for response in client.conversations_list(types="public_channel,private_channel"):
            for channel in response["channels"]:
                if channel["name"] == channel_input:
                    return channel["id"]
                elif fuzz.ratio(channel["name"], channel_input) > 80:
                    return channel["id"]
    except SlackApiError as e:
        print(f"Error listing channels: {e}")
        sys.exit(1)

    print(f"Channel not found: {channel_input}")
    sys.exit(1)

def create_investigation_message(pr_title, pr_url):
    return {
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"📥 *Incoming PR Failure Detected*\nWe're analyzing PR [{pr_title}]({pr_url}) triggered by a failed GitHub Action.\n\n⏳ Sit tight, we're investigating the root cause..."
                }
            }
        ]
    }

def create_summary_message(pr_title, pr_url, author, branch, what_failed, why_failed, how_to_fix, error_details, stack_trace_url):
    return {
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"🚨 *PR Failed*: [{pr_title}]({pr_url})"
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"👤 *Author*: {author}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"📂 *Branch*: `{branch}`"
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*❌ What Failed:*\n```\n{what_failed}\n```"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*❓ Why It Failed:*\n```\n{why_failed}\n```"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*🛠️ How to Fix:*\n```\n{how_to_fix}\n```"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "🔗 *Error Details:*\n```\n" + error_details.replace("\\n", "\n") + "\n```\n\n<" + stack_trace_url + "|View full stack trace>"
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "💬 Need help? Reply with `fix it step by step`, `explain the error`, `show logs here` or `show all affected files` for more details and guidance."
                    }
                ]
            }
        ]
    }

def send_slack_message(client, channel, message_type, *args):
    try:
        if message_type == "investigation":
            pr_title, pr_url = args
            blocks = create_investigation_message(pr_title, pr_url)
            fallback_text = f"Incoming PR Failure Detected\nWe're analyzing PR {pr_title} ({pr_url}) triggered by a failed GitHub Action.\nSit tight, we're investigating the root cause..."
        else:  # summary
            pr_title, pr_url, author, branch, what_failed, why_failed, how_to_fix, error_details, stack_trace_url = args
            blocks = create_summary_message(pr_title, pr_url, author, branch, what_failed, why_failed, how_to_fix, error_details, stack_trace_url)
            fallback_text = f"PR Failed: {pr_title}\nAuthor: {author}\nBranch: {branch}\nWhat Failed: {what_failed}\nWhy It Failed: {why_failed}\nHow to Fix: {how_to_fix}\nError Details: {error_details}\nStack Trace: {stack_trace_url}"
        
        response = client.chat_postMessage(
            channel=channel,
            blocks=blocks["blocks"],
            text=fallback_text
        )
        return {"success": True, "result": response.data}
    except SlackApiError as e:
        return {"success": False, "error": str(e)}

def main():
    """Main function to handle Slack message sending."""
    try:
        token = os.environ.get("SLACK_API_TOKEN")
        channel = os.environ.get("DESTINATION_CHANNEL")
        
        if not token:
            print(json.dumps({"success": False, "error": "SLACK_API_TOKEN is not set"}))
            sys.exit(1)
        if not channel:
            print(json.dumps({"success": False, "error": "DESTINATION_CHANNEL is not set"}))
            sys.exit(1)

        # Check if input is JSON
        if len(sys.argv) == 2 and sys.argv[1].startswith('{'):
            try:
                data = json.loads(sys.argv[1])
                message_type = "summary"
                args = [
                    data["pr_title"],
                    data["pr_url"],
                    data["author"],
                    data["branch"],
                    data["what_failed"],
                    data["why_failed"],
                    data["how_to_fix"],
                    data["error_details"],
                    data["stack_trace_url"]
                ]
            except (json.JSONDecodeError, KeyError) as e:
                print(json.dumps({"success": False, "error": f"Invalid JSON input: {str(e)}"}))
                sys.exit(1)
        else:
            # Handle command line arguments
            if len(sys.argv) < 2:
                print(json.dumps({"success": False, "error": "Usage: send_slack.py <message_type> [args...] or send_slack.py <json_data>"}))
                sys.exit(1)

            message_type = sys.argv[1]
            if message_type == "investigation":
                if len(sys.argv) != 4:
                    print(json.dumps({"success": False, "error": "Usage for investigation: send_slack.py investigation <pr_title> <pr_url>"}))
                    sys.exit(1)
                args = sys.argv[2:4]
            elif message_type == "summary":
                if len(sys.argv) != 11:
                    print(json.dumps({"success": False, "error": "Usage for summary: send_slack.py summary <pr_title> <pr_url> <author> <branch> <what_failed> <why_failed> <how_to_fix> <error_details> <stack_trace_url>"}))
                    sys.exit(1)
                args = sys.argv[2:11]
            else:
                print(json.dumps({"success": False, "error": "Invalid message type. Must be 'investigation' or 'summary'"}))
                sys.exit(1)

        client = WebClient(token=token)
        result = send_slack_message(client, channel, message_type, *args)
        print(json.dumps(result))
        
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}))
        sys.exit(1)

if __name__ == "__main__":
    main() 