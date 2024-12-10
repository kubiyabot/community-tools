# k8s_tools/__init__.py
from .initialization import initialize

# Run initialization when module is imported
initialize()

# Import tools after initialization
from .tools import *

__all__ = ['initialize']