# k8s_tools/__init__.py
from .kubewatch.initializer import initialize

# Run initialization when module is imported
initialize()

# Import tools after initialization
from .tools import *