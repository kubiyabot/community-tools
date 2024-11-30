import os
import sys
from typing import List, Dict, Any
from pathlib import Path
from .tools import load_terraform_tools

class InitializationError(Exception):
    """Error during terraform tools initialization."""
    def __init__(self, message: str, errors: List[Dict[str, Any]] = None):
        super().__init__(message)
        self.errors = errors or []

def initialize_terraform_tools() -> None:
    """Initialize terraform tools with proper error handling."""
    config_dir = os.path.join(os.path.dirname(__file__), '..', 'configs')
    
    # Verify config directory exists
    if not os.path.exists(config_dir):
        raise InitializationError(
            f"Configuration directory not found: {config_dir}"
        )
    
    # Verify at least one config file exists
    config_files = [f for f in os.listdir(config_dir) if f.endswith('.json')]
    if not config_files:
        raise InitializationError(
            f"No configuration files found in {config_dir}. "
            "Add at least one .json configuration file."
        )
    
    # Collect all errors during initialization
    initialization_errors = []
    
    try:
        # Attempt to load tools
        load_terraform_tools()
    except Exception as e:
        initialization_errors.append({
            "type": type(e).__name__,
            "message": str(e),
            "details": getattr(e, "errors", None)
        })
    
    # If there were any errors, raise them
    if initialization_errors:
        raise InitializationError(
            "Failed to initialize terraform tools",
            errors=initialization_errors
        )
    
    print("✅ Terraform tools initialized successfully")

# Initialize tools when package is imported
try:
    initialize_terraform_tools()
except InitializationError as e:
    print("❌ Terraform tools initialization failed:")
    print(f"Error: {str(e)}")
    if e.errors:
        print("\nDetailed errors:")
        for error in e.errors:
            print(f"- {error['type']}: {error['message']}")
            if error.get('details'):
                print(f"  Details: {error['details']}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Unexpected error during initialization: {str(e)}")
    sys.exit(1)

# Export the initialization function for manual reloading if needed
__all__ = ['initialize_terraform_tools']
