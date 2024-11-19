import logging
import sys
from pathlib import Path
from typing import List
from kubiya_sdk.tools.registry import tool_registry

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the project root to Python path
project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def register_tools() -> List:
    """Register all JIT access tools."""
    try:
        from .tools.generator import ToolGenerator
        
        # Create generator
        generator = ToolGenerator()
        
        # Generate tools
        tools = generator.generate_tools()
        
        if tools:
            # Register each tool
            for tool in tools:
                tool_registry.register("aws_jit", tool)
                logger.info(f"✅ Registered tool: {tool.name}")
            logger.info(f"Successfully registered {len(tools)} tools")
            return tools
        else:
            logger.warning("No tools were generated - check aws_jit_config.json")
            return []
            
    except Exception as e:
        logger.error(f"Error registering tools: {str(e)}")
        return []

# Register tools when package is imported
tools = register_tools()

# Export classes
from .tools.base import AWSJITTool
__all__ = ['AWSJITTool']

# Don't initialize here - let the user do it