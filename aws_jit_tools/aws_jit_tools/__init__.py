import logging
from .tools import initialize_tools

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize tools when module is imported
tools = initialize_tools()

# Export the tools
__all__ = ['tools', 'initialize_tools']
