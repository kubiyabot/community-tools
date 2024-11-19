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
        from .tools import ToolGenerator
        
        logger.info("Creating tool generator...")
        generator = ToolGenerator()
        
        logger.info("Generating tools...")
        tools = generator.generate_tools()
        
        logger.info(f"Successfully initialized {len(tools)} tools")
        return tools
    except Exception as e:
        logger.error(f"Failed to initialize tools: {str(e)}")
        raise

# Initialize tools when module is imported
tools = initialize_tools()

# Export necessary classes and tools
from .tools import AWSJITTool, ToolGenerator

__all__ = ['AWSJITTool', 'ToolGenerator', 'tools']
