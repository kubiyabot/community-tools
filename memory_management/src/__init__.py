from .tools import AddMemoryTool, DeleteMemoryTool, ListMemoriesTool

# Create tool instances
add_memory_tool = AddMemoryTool()
delete_memory_tool = DeleteMemoryTool()
list_memories_tool = ListMemoriesTool()

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