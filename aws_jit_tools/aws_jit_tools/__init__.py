import logging
import sys
from pathlib import Path

# Add the project root to Python path
project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

logger = logging.getLogger(__name__)

try:
    from .tools.generator import ToolGenerator
    
    # Create generator and register tools
    generator = ToolGenerator()
    tools = generator.generate_and_register_tools()
    
except Exception as e:
    logger.error(f"Error registering tools: {str(e)}")

# Only expose what's needed
from .tools.base import AWSJITTool

__all__ = ['ToolGenerator', 'AWSJITTool']

# Don't initialize here - let the user do it