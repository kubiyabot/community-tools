# k8s_tools/__init__.py
import sentry_sdk
from .initialization import initialize as init_kubewatch
from .utils.sentry_client import initialize_sentry

def initialize():
    """Initialize Kubernetes tools and KubeWatch configuration."""
    try:
        print("Starting Kubernetes tools initialization...")
        initialize_sentry()
        sentry_sdk.add_breadcrumb(
            category='initialization',
            message='Starting Kubernetes tools initialization',
            level='info'
        )
        
        init_kubewatch()
        
        sentry_sdk.capture_message(
            "Kubernetes tools initialization completed successfully",
            level='info'
        )
        print("Kubernetes tools initialization completed")
    except Exception as e:
        sentry_sdk.capture_exception(e)
        print(f"Failed to initialize Kubernetes tools: {str(e)}")
        raise

# Run initialization when module is imported
print("Loading Kubernetes tools module...")
initialize()
from .tools import *