from mermaid_tools.base import MermaidTool
from kubiya_sdk.tools import Arg, FileSpec
from kubiya_sdk.tools import tool_registry
import os

# Read the script content from the file
script_path = os.path.join(os.path.dirname(__file__), '..', 'scripts', 'share_diagram_on_slack.sh')
with open(script_path, 'r') as script_file:
    script_content = script_file.read()

share_diagram_on_slack_tool = MermaidTool(
    name="share_diagram_on_slack",
    description="Renders a Mermaid diagram from raw input and shares it on Slack using curl.",
    script_name="share_diagram_on_slack.sh",
    args=[
        Arg(name="diagram_content", type="str", description="Mermaid diagram content as a string.", required=True),
        Arg(name="slack_destination", type="str", description="Slack destination to send the diagram. Use '@username' for direct messages or '#channelname' for channels.", required=True),
        Arg(name="comment", type="str", description="Comment to include with the uploaded diagram. Defaults to 'Here is the diagram.'", required=False, default="Here is the diagram."),
        Arg(name="output_format", type="str", description="Output format for the diagram (svg, png, pdf). Defaults to 'png'.", required=False, default="png"),
        Arg(name="theme", type="str", description="Theme for rendering the diagram ('default', 'dark', 'forest', 'neutral'). Optional.", required=False),
        Arg(name="background_color", type="str", description="Background color or 'transparent'. Optional.", required=False),
    ],
    with_files=[
        FileSpec(
            destination="/tmp/scripts/share_diagram_on_slack.sh",
            content=script_content,
        ),
    ],
)

tool_registry.register("mermaid", share_diagram_on_slack_tool)
