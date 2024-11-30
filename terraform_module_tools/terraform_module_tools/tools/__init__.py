import logging
from typing import List
from kubiya_sdk.tools import Tool
from kubiya_sdk.tools.registry import tool_registry
from .dynamic_tool_loader import load_terraform_tools as _load_tools

logger = logging.getLogger(__name__)

def initialize_tools() -> List[Tool]:
    """Initialize and register all Terraform module tools."""
    try:
        logger.info("🔄 Initializing Terraform module tools...")
        
        # Load tools using the dynamic loader
        tools = _load_tools()
        
        # Register each tool
        for tool in tools:
            try:
                tool_registry.register("terraform_modules", tool)
                logger.info(f"✅ Registered tool: {tool.name}")
            except Exception as e:
                logger.error(f"❌ Failed to register tool {tool.name}: {str(e)}")
        
        return tools
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize tools: {str(e)}")
        return []

# Export only what's needed
__all__ = ['initialize_tools']