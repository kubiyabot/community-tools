import logging

logger = logging.getLogger(__name__)

try:
    from .tools.generator import ToolGenerator
    
    # Initialize tool generator
    generator = ToolGenerator()
    # Generate tools
    generator.generate_tools()
except ImportError as e:
    logger.warning(f"Import error: {str(e)}")
    logger.warning("Tools will be available after dependencies are installed")