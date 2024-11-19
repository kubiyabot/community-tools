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
    
    # Initialize tool generator
    generator = ToolGenerator()
    # Generate tools
    generator.generate_tools()
except ImportError as e:
    logger.warning(f"Import error: {str(e)}")
    logger.warning("Tools will be available after dependencies are installed")