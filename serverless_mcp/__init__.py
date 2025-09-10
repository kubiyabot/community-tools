# Main entry point for Kubiya to load serverless MCP tools.

from .loader import get_tools

# Kubiya will look for a 'tools' list or a 'get_tools' function.
# Ensure 'get_tools' is available for Kubiya SDK. 