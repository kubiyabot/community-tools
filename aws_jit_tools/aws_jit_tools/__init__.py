import logging
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the project root to Python path
project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def initialize_tools():
    """Initialize and register all JIT access tools."""
    try:
        from .tools.generator import ToolGenerator
        from kubiya_sdk.tools.registry import tool_registry
        
        logger.info("Creating tool generator...")
        generator = ToolGenerator()
        
        logger.info("Generating tools...")
        tools = generator.generate_tools()
        
        # Register each tool
        for tool in tools:
            tool_registry.register("aws_jit", tool)
            logger.info(f"Registered tool: {tool.name}")
        
        return tools
    except Exception as e:
        raise e

# Initialize tools when module is imported
tools = initialize_tools()

# Export necessary classes
from .tools.base import AWSJITTool
__all__ = ['AWSJITTool', 'initialize_tools']
