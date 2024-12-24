from typing import List
from kubiya_sdk.tools import Tool
from kubiya_sdk.tools.registry import tool_registry
import logging

from . import TerraformerTool, _initialize_provider_tools

logger = logging.getLogger(__name__)

def load_tools() -> List[Tool]:
    """Load all available tools."""
    tools = []
    
    try:
        # Try to initialize default tools first (without specific provider)
        default_tools = _initialize_provider_tools(None)
        tools.extend(default_tools)
        
        # Then initialize provider-specific tools
        providers = ['aws', 'gcp', 'azure']
        for provider in providers:
            provider_tools = _initialize_provider_tools(provider)
            tools.extend(provider_tools)
        
        if not tools:
            logger.warning("No tools were initialized")
            
    except Exception as e:
        logger.error(f"Failed to load tools: {str(e)}")
    
    return tools

def register_tools():
    """Register all tools with the tool registry."""
    tools = load_tools()
    if not tools:
        logger.warning("No tools to register")
        return
        
    for tool in tools:
        try:
            tool_registry.register("terraform_module_tools", tool)
            logger.info(f"Registered tool: {tool.name}")
        except Exception as e:
            logger.error(f"Failed to register tool {tool.name}: {str(e)}")

