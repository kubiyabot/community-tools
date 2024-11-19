import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def initialize_tools():
    """Initialize and register all JIT access tools."""
    try:
        logger.info("Initializing tools...")
        # Delayed import to avoid potential circular imports
        from .tools import initialize_tools as tools_init

        tools = tools_init()

        logger.info(f"Successfully initialized {len(tools)} tools")
        return tools
    except Exception as e:
        logger.error(f"Failed to initialize tools: {str(e)}")
        raise

# Initialize tools when module is imported
tools = initialize_tools()

# Export all components
from .tools import AWSJITTool, COMMON_FILES, COMMON_ENV

__all__ = [
    'AWSJITTool',
    'tools',
    'COMMON_FILES',
    'COMMON_ENV'
]
