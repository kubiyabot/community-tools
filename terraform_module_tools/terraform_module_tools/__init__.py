from .tools import (
    initialize_tools,
    create_terraform_module_tool,
    initialize_module_tools,
    TerraformModuleTool
)

# Initialize tools on module import
try:
    from kubiya_sdk.tools.registry import tool_registry
    config = tool_registry.dynamic_config
    if config:
        initialize_tools(config)
except Exception as e:
    import logging
    logger = logging.getLogger(__name__)
    logger.error(f"Failed to initialize tools: {str(e)}")

__all__ = [
    'initialize_tools',
    'create_terraform_module_tool',
    'initialize_module_tools',
    'TerraformModuleTool'
]
