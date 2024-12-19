# k8s_tools/__init__.py
import os

def initialize():
    """Initialize JIT tools and Enforcer configuration."""
    try:
        print("Starting Enforcer initialization...")
        from .initialization import initialize as init_enforcer
        init_enforcer()
        print("Enforcer initialization completed")
    except Exception as e:
        print(f"Failed to initialize Enforcer : {str(e)}")
        raise

# Run initialization when module is imported
print("Loading Kubernetes tools module...")


# Import tools after initialization
from . import *
