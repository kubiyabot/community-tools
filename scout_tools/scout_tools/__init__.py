import logging
from .tools import aws_scan_tool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Export the tools
__all__ = ['aws_scan_tool']
