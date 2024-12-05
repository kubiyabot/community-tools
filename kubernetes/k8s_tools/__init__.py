# k8s_tools/__init__.py
import os
import sys
from .utils.script_runner import run_script

def initialize():
    """Initialize the Kubernetes tools environment."""
    init_script = os.path.join(os.path.dirname(__file__), 'utils', 'init_cluster.sh')
    try:
        # Run initialization script
        run_script(f"bash {init_script}")
        print("✅ Kubernetes tools initialized successfully")
    except Exception as e:
        print(f"❌ Initialization failed: {str(e)}", file=sys.stderr)
        sys.exit(1)

# Run initialization when module is imported
initialize()

# Import tools after initialization
from .tools import *