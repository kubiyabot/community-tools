"""Tool registration module for Python Executor tools."""

from kubiya_sdk.tools.registry import tool_registry
from .tools.executor import python_executor
from .tools.jupyter_executor import jupyter_executor

def register_tools():
    """Register all Python Executor tools with Kubiya."""
    # Register Python code executor
    tool_registry.register("python_executor", python_executor)
    
    # Register Jupyter notebook executor
    tool_registry.register("jupyter_executor", jupyter_executor)

    return {
        "python_executor": python_executor,
        "jupyter_executor": jupyter_executor
    } 