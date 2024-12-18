# k8s_tools/__init__.py
import os
from .kubewatch.builder import KubeWatchConfigBuilder

def initialize():
    """Initialize Kubernetes tools and KubeWatch configuration."""
    try:
        print("Starting Kubernetes tools initialization...")
        from .initialization import initialize as init_kubewatch
        init_kubewatch()
        print("Kubernetes tools initialization completed")
    except Exception as e:
        print(f"Failed to initialize Kubernetes tools: {str(e)}")
        raise

# Run initialization when module is imported
print("Loading Kubernetes tools module...")
initialize()

# Import tools after initialization
from .tools import *
