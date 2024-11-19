import logging
import sys
from pathlib import Path

# Add the project root to Python path
project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

logger = logging.getLogger(__name__)

# Only expose what's needed
from .tools.generator import ToolGenerator
from .tools.base import AWSJITTool

__all__ = ['ToolGenerator', 'AWSJITTool']

# Don't initialize here - let the user do it