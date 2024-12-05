from mermaid_tools.base import MermaidTool
from kubiya_sdk.tools import Arg, FileSpec
from kubiya_sdk.tools import tool_registry
import os

# Read the script content
script_path = os.path.join(os.path.dirname(__file__), '..', 'scripts', 'share_diagram_on_slack.sh')
with open(script_path, 'r') as script_file:
    script_content = script_file.read()

# Read default CSS content
css_path = os.path.join(os.path.dirname(__file__), '..', 'styles', 'default.css')
with open(css_path, 'r') as css_file:
    default_css_content = css_file.read()

share_diagram_on_slack_tool = MermaidTool(
    name="share_diagram_on_slack",
    description="Renders a Mermaid diagram and shares it on Slack",
    args=[
        Arg(
            name="diagram_content",
            type="str",
            description="Mermaid diagram content as a string",
            required=True
        ),
        Arg(
            name="slack_destination",
            type="str",
            description="Slack destination (#channel or @user, channel ID or user ID is also accepted)",
            required=True
        ),
        Arg(
            name="comment",
            type="str",
            description="Comment to include with the diagram",
            required=False,
            default="Here is the diagram."
        ),
        Arg(
            name="output_format",
            type="str",
            description="Output format (png, svg)",
            required=False,
            default="png"
        ),
    ],
    with_files=[
        FileSpec(
            destination="/tmp/scripts/share_diagram_on_slack.sh",
            content=script_content,
        ),
        FileSpec(
            destination="/tmp/styles/default.css",
            content=default_css_content,
        ),
    ],
    secrets=["SLACK_API_TOKEN"],
)

tool_registry.register("mermaid", share_diagram_on_slack_tool)