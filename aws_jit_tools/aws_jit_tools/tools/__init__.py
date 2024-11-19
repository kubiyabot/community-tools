import logging
from kubiya_sdk.tools.registry import tool_registry
from .generator import generate_tools
from .base import AWSJITTool

logger = logging.getLogger(__name__)

def initialize_tools():
    """Initialize and register all JIT access tools."""
    try:
        logger.info("Generating AWS JIT access tools...")
        tools = generate_tools()
        
        # Register each tool
        for tool in tools:
            tool_registry.register("aws_jit", tool)
            logger.info(f"Registered tool: {tool.name}")
            
        logger.info(f"Successfully initialized {len(tools)} tools")
        return tools
    except Exception as e:
        logger.error(f"Failed to initialize tools: {str(e)}")
        raise

# Export all necessary components
__all__ = ['initialize_tools', 'generate_tools', 'AWSJITTool']
