import logging
from typing import List
from kubiya_sdk.tools import Tool
from kubiya_sdk.tools.registry import tool_registry
from .dynamic_tool_loader import load_terraform_tools as _load_tools

logger = logging.getLogger(__name__)

def initialize_tools(config_dir: str = None) -> List[Tool]:
    """Initialize and register all Terraform module tools."""
    try:
        logger.info("🔄 Initializing Terraform module tools...")
        
        # Load tools using the dynamic loader
        tools = _load_tools(config_dir)
        
        if not tools:
            logger.warning("No tools were loaded from the dynamic loader")
            return []
            
        registered_tools = []
        # Register each tool
        for tool in tools:
            try:
                tool_registry.register("terraform_modules", tool)
                logger.info(f"✅ Registered tool: {tool.name}")
                registered_tools.append(tool)
            except Exception as e:
                logger.error(f"❌ Failed to register tool {getattr(tool, 'name', 'unknown')}: {str(e)}")
        
        return registered_tools
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize tools: {str(e)}", exc_info=True)
        return []

# Export only what's needed
__all__ = ['initialize_tools']