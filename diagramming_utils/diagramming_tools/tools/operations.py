from kubiya_sdk.tools import Arg
from .base import DiagrammingTool
from kubiya_sdk.tools.registry import tool_registry

mermaid_render_and_share_tool = DiagrammingTool(
    name="mermaid_render_and_share",
    description="Renders a Mermaid diagram from provided content and optionally shares it",
    content="""
    #!/bin/bash
    set -e

    # Create a temporary file for the Mermaid content
    MERMAID_FILE=$(mktemp)
    echo "$mermaid_content" > $MERMAID_FILE

    # Generate the diagram
    mmdc -i $MERMAID_FILE -o /tmp/diagram.svg -b transparent

    # Share via Slack if requested
    if [ "$share_on_slack" = "true" ] && [ -n "$SLACK_API_TOKEN" ] && [ -n "$slack_channel" ]; then
        curl -F file=@/tmp/diagram.svg \
             -F "channels=$slack_channel" \
             -F "initial_comment=$initial_comment" \
             -F "title=$title" \
             -H "Authorization: Bearer $SLACK_API_TOKEN" \
             https://slack.com/api/files.upload
        echo "Diagram shared on Slack in channel: $slack_channel"
    else
        echo "Diagram generated and saved as /tmp/diagram.svg"
        cat /tmp/diagram.svg | base64
    fi

    # Clean up
    rm $MERMAID_FILE
    rm /tmp/diagram.svg
    """,
    args=[
        Arg(name="mermaid_content", type="str", description="Mermaid diagram content as string (should be valid mermaid syntax)", required=True),
        Arg(name="share_on_slack", type="bool", description="Whether to share the diagram on Slack", required=False),
        Arg(name="slack_channel", type="str", description="Slack channel to share the diagram (required if share_on_slack is true)", required=False),
        Arg(name="initial_comment", type="str", description="Initial comment for the Slack message", required=False),
        Arg(name="title", type="str", description="Title for the diagram in Slack", required=False),
    ],
)

# Register all tools
for tool in [mermaid_render_and_share_tool]:
    tool_registry.register("diagramming", tool)

# Register the tool
tool_registry.register("diagramming", mermaid_render_and_share_tool)
