from mermaid_tools.base import MermaidTool
from kubiya_sdk.tools import Arg
from kubiya_sdk.tools import tool_registry

share_diagram_on_slack_tool = MermaidTool(
    name="share_diagram_on_slack",
    description="Renders a Mermaid diagram from raw input and shares it on Slack...",
    content="""
# Function to display engaging messages
print_with_delay() {
    message="$1"
    echo "$message"
    sleep 1
}

# ... rest of your script ...
""",
    args=[
        # Your arguments here
    ],
)

tool_registry.register("mermaid", share_diagram_on_slack_tool)
