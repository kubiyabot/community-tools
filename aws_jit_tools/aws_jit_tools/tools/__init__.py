import logging
from pathlib import Path
import sys

# Add the project root to Python path
project_root = str(Path(__file__).resolve().parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

logger = logging.getLogger(__name__)

try:
    from .generator import ToolGenerator
    from kubiya_sdk.tools.registry import tool_registry

    # Create generator
    generator = ToolGenerator()
    
    # Generate tools and register them
    tools = generator.generate_tools()
    
    # Register each tool
    if tools:
        for tool in tools:
            tool_registry.register("aws_jit", tool)
            logger.info(f"✅ Registered tool: {tool.name}")
        logger.info(f"Successfully registered {len(tools)} tools")
    else:
        logger.warning("No tools were generated - check aws_jit_config.json")

except Exception as e:
    logger.error(f"Error registering tools: {str(e)}")

# Only expose what's needed
from .base import AWSJITTool

__all__ = ['ToolGenerator', 'AWSJITTool']
