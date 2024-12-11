# k8s_tools/__init__.py
import os
from .utils.script_runner import run_script

def initialize():
    """Initialize Kubernetes tools and KubeWatch configuration."""
    init_script = os.path.join(os.path.dirname(__file__), 'utils', 'init_cluster.sh')
    run_script(init_script)

# Run initialization when module is imported
initialize()

# Import tools after initialization
from .tools import *

__all__ = ['initialize']