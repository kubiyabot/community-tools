from kubiya_sdk.tools import Arg
from .base import DiagrammingTool
from kubiya_sdk.tools.registry import tool_registry

mermaid_render_tool = DiagrammingTool(
    name="mermaid_render",
    description="Renders a Mermaid diagram and returns the result as a string",
    content="""
    #!/bin/bash
    set -e
    echo "$mermaid_content" | mmdc -o /tmp/output.mmd
    cat /tmp/output.mmd
    """,
    args=[
        Arg(name="mermaid_content", type="str", description="Mermaid diagram content", required=True),
    ],
)

mermaid_to_svg_tool = DiagrammingTool(
    name="mermaid_to_svg",
    description="Converts a Mermaid diagram to SVG format",
    content="""
    #!/bin/bash
    set -e
    echo "$mermaid_content" | mmdc -o /tmp/output.svg
    cat /tmp/output.svg | base64
    """,
    args=[
        Arg(name="mermaid_content", type="str", description="Mermaid diagram content", required=True),
    ],
)

mermaid_to_png_tool = DiagrammingTool(
    name="mermaid_to_png",
    description="Converts a Mermaid diagram to PNG format",
    content="""
    #!/bin/bash
    set -e
    echo "$mermaid_content" | mmdc -o /tmp/output.png
    cat /tmp/output.png | base64
    """,
    args=[
        Arg(name="mermaid_content", type="str", description="Mermaid diagram content", required=True),
    ],
)

share_diagram_tool = DiagrammingTool(
    name="share_diagram",
    description="Shares a mermaid diagram via Slack or email",
    content="""
    #!/bin/bash
    set -e
    
    # Generate the diagram
    echo "$diagram_content" | mmdc -o /tmp/diagram.$output_format
    
    if [ "$share_method" == "slack" ]; then
        # Share via Slack
        curl -F file=@/tmp/diagram.$output_format -F "channels=$slack_channel" -H "Authorization: Bearer $SLACK_API_TOKEN" https://slack.com/api/files.upload
    elif [ "$share_method" == "email" ]; then
        # Share via email (this is a placeholder, you'd need to implement email sending logic)
        echo "Sending email to $email_recipient with diagram attached"
    else
        echo "Invalid share method. Use 'slack' or 'email'."
        exit 1
    fi
    """,
    args=[
        Arg(name="diagram_content", type="str", description="Mermaid diagram content (as a string, valid mermaid syntax)", required=True),
        Arg(name="output_format", type="str", description="Output format (svg or png)", required=True),
        Arg(name="share_method", type="str", description="Sharing method (slack or email)", required=True),
        Arg(name="slack_channel", type="str", description="Slack channel to share to (if using Slack)", required=False),
        Arg(name="email_recipient", type="str", description="Email recipient (if using email)", required=False),
    ],
)

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
for tool in [mermaid_render_tool, mermaid_to_svg_tool, mermaid_to_png_tool, share_diagram_tool]:
    tool_registry.register("diagramming", tool)

# Register the tool
tool_registry.register("diagramming", mermaid_render_and_share_tool)
