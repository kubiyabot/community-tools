from ..base import MermaidTool
from kubiya_sdk.tools import Arg

share_diagram_on_slack_tool = MermaidTool(
    name="share_diagram_on_slack",
    description="Shares a diagram file on Slack using slack-cli.",
    content="""
    #!/bin/bash
    set -euo pipefail

    # Check if diagram_file is provided
    if [ -z "${diagram_file:-}" ]; then
        echo "❌ Error: 'diagram_file' must be provided."
        exit 1
    fi

    # Check if Slack credentials are provided
    if [ -z "${SLACK_API_TOKEN:-}" ] || [ -z "${SLACK_CHANNEL_ID:-}" ]; then
        echo "❌ Error: 'SLACK_API_TOKEN' and 'SLACK_CHANNEL_ID' must be set."
        exit 1
    fi

    echo "📤 Sharing diagram on Slack..."
    export SLACK_CLI_TOKEN="$SLACK_API_TOKEN"

    # Send file to Slack channel, and optionally to a thread if SLACK_THREAD_TS is set
    if [ -n "${SLACK_THREAD_TS:-}" ]; then
        slack file upload "$diagram_file" "$SLACK_CHANNEL_ID" --thread "${SLACK_THREAD_TS}" --comment "${comment:-Here is the diagram.}"
    else
        slack file upload "$diagram_file" "$SLACK_CHANNEL_ID" --comment "${comment:-Here is the diagram.}"
    fi
    echo "✅ Diagram shared on Slack channel $SLACK_CHANNEL_ID."
    """,
    args=[
        Arg(name="diagram_file", type="str", description="Path to the diagram file to share", required=True),
        Arg(name="comment", type="str", description="Comment to include with the uploaded file", required=False),
    ],
) 