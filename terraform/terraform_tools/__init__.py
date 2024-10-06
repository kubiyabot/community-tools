from .tools.terraform_operations import create_terraform_tool, tool_registry

# Get all registered Terraform tools
terraform_tools = tool_registry.get_tools("terraform")

# Create a dictionary of tool names to tool objects
terraform_tool_dict = {tool.name: tool for tool in terraform_tools}

# Add the tools to the module's namespace
globals().update(terraform_tool_dict)

__all__ = list(terraform_tool_dict.keys())