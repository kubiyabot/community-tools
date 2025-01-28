"""Python Executor Tools for Kubiya."""

__version__ = "0.1.0"

from .tools import python_executor, jupyter_executor
from kubiya_sdk.tools.registry import tool_registry

# Register tools
tool_registry.register("python_executor", python_executor)
tool_registry.register("jupyter_executor", jupyter_executor)

__all__ = ['python_executor', 'jupyter_executor']