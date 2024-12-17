from .add_memory import add_memory_tool, AddMemoryTool
from .delete_memory import delete_memory_tool, DeleteMemoryTool
from .list_memories import list_memories_tool, ListMemoriesTool

# Register tools
from kubiya_sdk.tools.registry import tool_registry
tool_registry.register("memory_management", add_memory_tool)
tool_registry.register("memory_management", delete_memory_tool)
tool_registry.register("memory_management", list_memories_tool)

__all__ = [
    "add_memory_tool",
    "delete_memory_tool",
    "list_memories_tool",
    "AddMemoryTool",
    "DeleteMemoryTool",
    "ListMemoriesTool"
]
