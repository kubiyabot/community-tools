from .render_diagram import render_diagram_tool
from .share_diagram_on_slack import share_diagram_on_slack_tool
from .convert_markdown import convert_markdown_tool

from kubiya_sdk.tools.registry import tool_registry

tool_registry.register("mermaid", render_diagram_tool)
tool_registry.register("mermaid", share_diagram_on_slack_tool)
tool_registry.register("mermaid", convert_markdown_tool)
