from typing import Dict, Any, List
from .dynamic_tool_loader import load_terraform_tools as _load_tools

def load_terraform_tools() -> None:
    """
    Load and register all Terraform tools from configuration files.
    
    Raises:
        Exception: If any critical error occurs during tool loading
    """
    errors = []
    
    try:
        _load_tools()
    except Exception as e:
        errors.append({
            "type": type(e).__name__,
            "message": str(e),
            "details": getattr(e, "errors", None)
        })
    
    if errors:
        error_msg = "Failed to load terraform tools:\n"
        for error in errors:
            error_msg += f"\n- {error['type']}: {error['message']}"
            if error.get('details'):
                error_msg += f"\n  Details: {error['details']}"
        raise Exception(error_msg)

# Export only what's needed
__all__ = ['load_terraform_tools']