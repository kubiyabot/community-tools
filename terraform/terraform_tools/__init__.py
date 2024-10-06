from .tools import terraform_operations
from kubiya_sdk.tools.registry import tool_registry

# Get all registered Terraform tools
terraform_tools = tool_registry["terraform"]

# Create a dictionary of tool names to tool objects
terraform_tool_dict = {tool.name.replace("terraform_", ""): tool for tool in terraform_tools}

# Add the tools to the module's namespace
globals().update(terraform_tool_dict)

__all__ = list(terraform_tool_dict.keys())
