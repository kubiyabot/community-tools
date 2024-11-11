from mermaid_tools.base import MermaidTool
from kubiya_sdk.tools import Arg, FileSpec
from kubiya_sdk.tools import tool_registry
import os

# Read the script content
script_path = os.path.join(os.path.dirname(__file__), '..', 'scripts', 'share_diagram_on_slack.sh')
with open(script_path, 'r') as script_file:
    script_content = script_file.read()

share_diagram_on_slack_tool = MermaidTool(
    name="share_diagram_on_slack",
    description="Renders a Mermaid diagram from raw input and shares it on Slack using slack-cli.",
    args=[
        Arg(
            name="diagram_content",
            type="str",
            description="""Mermaid diagram content as a string. Example: