# k8s_tools/__init__.py
import os
from .utils.script_runner import run_script, ScriptExecutionError

def initialize():
    """Initialize Kubernetes tools and KubeWatch configuration."""
    init_script = os.path.join(os.path.dirname(__file__), 'utils', 'init_cluster.sh')
    try:
        print(f"Attempting to initialize Kubernetes tools...")
        run_script(init_script)
    except ScriptExecutionError as e:
        # Format a user-friendly error message
        error_msg = (
            f"Failed to initialize Kubernetes tools\n\n"
            f"Unable to install dependencies on the cluster:\n"
            f"{e.error_output}\n\n"
            f"Standard output:\n{e.output}"
        )
        raise Exception(error_msg)
    except Exception as e:
        raise Exception(f"Unexpected error during initialization: {str(e)}")

# Run initialization when module is imported
initialize()

# Import tools after initialization
from .tools import *

__all__ = ['initialize']