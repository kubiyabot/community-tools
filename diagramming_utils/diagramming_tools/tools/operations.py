from kubiya_sdk.tools import Arg
from .base import DiagrammingTool
from kubiya_sdk.tools.registry import tool_registry

mermaid_render_and_share_tool = DiagrammingTool(
    name="mermaid_render_and_share",
    description="Renders a Mermaid diagram from provided content and optionally shares it",
    content="""
    # Create a temporary file for the Mermaid content
    MERMAID_FILE=$(mktemp)
    echo "$mermaid_content" > "$MERMAID_FILE"

    # Generate the diagram
    if ./node_modules/.bin/mmdc -i "$MERMAID_FILE" -o /tmp/diagram.svg -b transparent; then
        echo "Diagram generated successfully."
    else
        echo "Error generating diagram." >&2
        exit 1
    fi

    # Share via Slack if requested
    if [ "$share_on_slack" = "true" ] && [ -n "$SLACK_API_TOKEN" ] && [ -n "$slack_channel" ]; then
        if curl -F file=@/tmp/diagram.svg \
                 -F "channels=$slack_channel" \
                 -F "initial_comment=$initial_comment" \
                 -F "title=$title" \
                 -H "Authorization: Bearer $SLACK_API_TOKEN" \
                 https://slack.com/api/files.upload; then
            echo "Diagram shared on Slack in channel: $slack_channel"
        else
            echo "Error sharing diagram on Slack." >&2
            exit 1
        fi
    else
        echo "Diagram generated and saved as /tmp/diagram.svg"
    fi

    # Clean up
    rm -f "$MERMAID_FILE" /tmp/diagram.svg
    """,
    args=[
        Arg(name="mermaid_content", type="str", description="Mermaid diagram content as string (should be valid mermaid syntax)", required=True),
        Arg(name="share_on_slack", type="bool", description="Whether to share the diagram on Slack", required=False),
        Arg(name="slack_channel", type="str", description="Slack channel to share the diagram (required if share_on_slack is true)", required=False),
        Arg(name="initial_comment", type="str", description="Initial comment for the Slack message", required=False),
        Arg(name="title", type="str", description="Title for the diagram in Slack", required=False),
    ],
)

# Register the tool
tool_registry.register("diagramming", mermaid_render_and_share_tool)
