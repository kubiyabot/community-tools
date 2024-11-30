from .tools import load_terraform_tools

# Load tools automatically when package is imported
load_terraform_tools()

# Export the loader function in case it needs to be called again
__all__ = ['load_terraform_tools']
