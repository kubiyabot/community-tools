from typing import List
from kubiya_sdk.tools import Tool
from kubiya_sdk.tools.registry import tool_registry
import logging

from . import TerraformerTool, _initialize_provider_tools

logger = logging.getLogger(__name__)

def load_tools() -> List[Tool]:
    """Load all available tools."""
    tools = []
    
    # Initialize tools for each provider
    providers = ['aws', 'gcp', 'azure']
    for provider in providers:
        provider_tools = _initialize_provider_tools(provider)
        tools.extend(provider_tools)
    
    return tools

def register_tools():
    """Register all tools with the tool registry."""
    tools = load_tools()
    for tool in tools:
        tool_registry.register("terraform_module_tools", tool)

