# k8s_tools/__init__.py

# Import tools first
from .tools import *

# Then run initialization
from .initialization import initialize
initialize()

__all__ = ['initialize']