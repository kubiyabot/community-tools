from .tools import generate_iam_access_tools

# Generate tools when module is imported
generate_iam_access_tools()

__all__ = ['generate_iam_access_tools'] 