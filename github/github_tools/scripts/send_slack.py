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

def _truncate_error_details(error_details, max_lines=3):
    """Truncate error details to max_lines and add ellipsis on a new line if needed."""
    # First, handle escaped newlines
    processed_details = error_details.replace(r'\\n', chr(10))
    
    # Split into lines
    lines = processed_details.split('\n')
    
    # Debug logging
    logger.info(f"Error details truncation: {len(lines)} lines found (max: {max_lines})")
    logger.info(f"Lines: {lines}")
    
    # If we have more lines than allowed, truncate and add ellipsis on new line
    if len(lines) > max_lines:
        truncated_lines = lines[:max_lines]
        truncated_lines.append('...')
        logger.info(f"Truncated to {max_lines} lines with ellipsis on new line")
        return '\n'.join(truncated_lines)
    
    # No truncation needed
    logger.info("No truncation needed - returning full content")
    return processed_details

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

def create_summary_message(pr_title, pr_url, author, branch, what_failed, why_failed, how_to_fix, error_details, stack_trace_url, triggered_on):
    # Debug output to help identify parameter issues
    logger.info(f"Creating summary message with parameters:")
    logger.info(f"  pr_title: '{pr_title}'")
    logger.info(f"  pr_url: '{pr_url}'")
    logger.info(f"  author: '{author}'")
    logger.info(f"  branch: '{branch}'")
    logger.info(f"  what_failed: '{what_failed}'")
    logger.info(f"  why_failed: '{why_failed}'")
    logger.info(f"  how_to_fix: '{how_to_fix}'")
    logger.info(f"  error_details: '{error_details}'")
    logger.info(f"  stack_trace_url: '{stack_trace_url}'")
    logger.info(f"  triggered_on: '{triggered_on}'")
    
    # Parse and format the ISO timestamp to human-readable format
    from datetime import datetime
    try:
        # Parse ISO format timestamp
        dt = datetime.fromisoformat(triggered_on.replace('Z', '+00:00'))
        formatted_time = dt.strftime("%b %d, %Y at %I:%M %p UTC")
    except:
        # Fallback to provided string if parsing fails
        formatted_time = triggered_on
    
    # Extract PR number from URL if possible, otherwise use title
    pr_number = ""
    if "/pull/" in pr_url:
        try:
            pr_number = "#" + pr_url.split("/pull/")[1].split("/")[0] + " - "
        except:
            pr_number = ""
    
    return {
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"🚨 PR Failure: {pr_number}{pr_title}",
                    "emoji": True
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
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"🔗 <{pr_url}|View PR in GitHub>"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"🕒 *Triggered On*: {formatted_time}"
                    }
                ]
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"▸ *What Failed*\n```{what_failed}```"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"▸ *Why It Failed*\n```{why_failed}```"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"▸ *How to Fix*\n```{how_to_fix}```"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"▸ *Error Details*\n```{_truncate_error_details(error_details)}```\n\n<{stack_trace_url}|View full stack trace>"
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
            },
            {
                "type": "divider"
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "plain_text",
                        "text": " ",
                        "emoji": True
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
            pr_title, pr_url, author, branch, what_failed, why_failed, how_to_fix, error_details, stack_trace_url, triggered_on = args
            blocks = create_summary_message(pr_title, pr_url, author, branch, what_failed, why_failed, how_to_fix, error_details, stack_trace_url, triggered_on)
            fallback_text = f"PR Failed: {pr_title}\nAuthor: {author}\nBranch: {branch}\nWhat Failed: {what_failed}\nWhy It Failed: {why_failed}\nHow to Fix: {how_to_fix}\nError Details: {error_details}\nStack Trace: {stack_trace_url}"
        
        response = client.chat_postMessage(
            channel=channel,
            blocks=blocks["blocks"],
            text=fallback_text
        )
        return {"success": True, "result": {"ok": response["ok"], "channel": response["channel"], "ts": response["ts"]}}
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
                    data["stack_trace_url"],
                    data["triggered_on"]
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
                if len(sys.argv) != 12:
                    print(json.dumps({"success": False, "error": "Usage for summary: send_slack.py summary <pr_title> <pr_url> <author> <branch> <what_failed> <why_failed> <how_to_fix> <error_details> <stack_trace_url> <triggered_on>"}))
                    sys.exit(1)
                args = sys.argv[2:12]
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