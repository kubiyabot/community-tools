from typing import List
from .base import SlackBaseTool
from kubiya_sdk.tools import Arg
from kubiya_sdk.tools.registry import tool_registry

class SlackTools:
    """Slack notification and communication tools."""
    
    def __init__(self):
        """Initialize and register all Slack tools."""
        tools = [
            self.post_message(),
            self.post_error_report(),
            self.search_messages(),
            self.get_channel_history()
        ]
        
        for tool in tools:
            tool_registry.register("slack", tool)

    def post_message(self) -> SlackBaseTool:
        """Post a message to a Slack channel."""
        return SlackBaseTool(
            name="post_message",
            description="Post a message to a Slack channel",
            content="""
            #!/usr/bin/env python3
            import os
            import json
            from slack_sdk import WebClient
            from slack_sdk.errors import SlackApiError

            # Initialize Slack client
            client = WebClient(token=os.environ['SLACK_BOT_TOKEN'])

            # Prepare message
            channel = os.environ['channel']
            text = os.environ['text']
            blocks = json.loads(os.environ.get('blocks', 'null'))

            try:
                # Post message
                response = client.chat_postMessage(
                    channel=channel,
                    text=text,
                    blocks=blocks
                )
                print(json.dumps(response.data))
            except SlackApiError as e:
                print(json.dumps({"error": str(e)}))
            """,
            args=[
                Arg(name="channel",
                    description="Channel to post to",
                    required=True),
                Arg(name="text",
                    description="Message text",
                    required=True),
                Arg(name="blocks",
                    description="Message blocks in JSON format",
                    required=False)
            ],
            image="python:3.9-slim"
        )

    def post_error_report(self) -> SlackBaseTool:
        """Post a formatted error report to Slack."""
        return SlackBaseTool(
            name="post_error_report",
            description="Post a formatted error report to Slack",
            content="""
            #!/usr/bin/env python3
            import os
            import json
            from slack_sdk import WebClient
            from slack_sdk.errors import SlackApiError

            # Initialize Slack client
            client = WebClient(token=os.environ['SLACK_BOT_TOKEN'])

            # Prepare error report blocks
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "🚨 Error Report"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Description:*\\n{os.environ['error_description']}"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Request ID:*\\n{os.environ.get('request_id', 'N/A')}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Service:*\\n{os.environ.get('service', 'N/A')}"
                        }
                    ]
                }
            ]

            try:
                # Post error report
                response = client.chat_postMessage(
                    channel=os.environ['channel'],
                    text=f"Error Report: {os.environ['error_description']}",
                    blocks=blocks
                )
                print(json.dumps(response.data))
            except SlackApiError as e:
                print(json.dumps({"error": str(e)}))
            """,
            args=[
                Arg(name="channel",
                    description="Channel to post to",
                    required=True),
                Arg(name="error_description",
                    description="Description of the error",
                    required=True),
                Arg(name="request_id",
                    description="Request ID for tracking",
                    required=False),
                Arg(name="service",
                    description="Affected service name",
                    required=False)
            ],
            image="python:3.9-slim"
        )

    def search_messages(self) -> SlackBaseTool:
        """Search messages in Slack."""
        return SlackBaseTool(
            name="search_messages",
            description="Search messages in Slack channels",
            content="""
            #!/usr/bin/env python3
            import os
            import json
            from slack_sdk import WebClient
            from slack_sdk.errors import SlackApiError

            # Initialize Slack client
            client = WebClient(token=os.environ['SLACK_BOT_TOKEN'])

            try:
                # Search messages
                response = client.search_messages(
                    query=os.environ['query'],
                    sort=os.environ.get('sort', 'score'),
                    count=int(os.environ.get('count', '100'))
                )

                # Format results
                messages = [{
                    'text': msg['text'],
                    'user': msg['username'],
                    'channel': msg['channel']['name'],
                    'timestamp': msg['ts'],
                    'permalink': msg['permalink']
                } for msg in response.data['messages']['matches']]

                print(json.dumps(messages))
            except SlackApiError as e:
                print(json.dumps({"error": str(e)}))
            """,
            args=[
                Arg(name="query",
                    description="Search query",
                    required=True),
                Arg(name="sort",
                    description="Sort results by (score/timestamp)",
                    required=False),
                Arg(name="count",
                    description="Number of results to return",
                    required=False)
            ],
            image="python:3.9-slim"
        )

    def get_channel_history(self) -> SlackBaseTool:
        """Get message history for a channel."""
        return SlackBaseTool(
            name="get_channel_history",
            description="Get message history for a Slack channel",
            content="""
            #!/usr/bin/env python3
            import os
            import json
            from slack_sdk import WebClient
            from slack_sdk.errors import SlackApiError

            # Initialize Slack client
            client = WebClient(token=os.environ['SLACK_BOT_TOKEN'])

            try:
                # Get channel history
                response = client.conversations_history(
                    channel=os.environ['channel'],
                    limit=int(os.environ.get('limit', '100'))
                )

                # Format messages
                messages = [{
                    'text': msg['text'],
                    'user': msg['user'],
                    'timestamp': msg['ts'],
                    'thread_ts': msg.get('thread_ts')
                } for msg in response.data['messages']]

                print(json.dumps(messages))
            except SlackApiError as e:
                print(json.dumps({"error": str(e)}))
            """,
            args=[
                Arg(name="channel",
                    description="Channel ID or name",
                    required=True),
                Arg(name="limit",
                    description="Number of messages to return",
                    required=False)
            ],
            image="python:3.9-slim"
        )

# Initialize when module is imported
SlackTools() 