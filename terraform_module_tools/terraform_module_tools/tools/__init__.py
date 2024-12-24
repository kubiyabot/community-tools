import logging
from typing import List, Dict, Any
from kubiya_sdk.tools import Tool
from kubiya_sdk.tools.registry import tool_registry
from .terraformer_tool import TerraformerTool, _initialize_provider_tools
from .terraform_module_tool import TerraformModuleTool
from .module_tools import create_terraform_module_tool, initialize_module_tools

logger = logging.getLogger(__name__)

def initialize_tools(config: Dict[str, Any]) -> List[Tool]:
    """Initialize all Terraform tools from configuration."""
    tools = []
    try:
        # Initialize terraformer tools if enabled
        if config.get('terraform', {}).get('enable_reverse_terraform'):
            providers = TerraformerTool.get_enabled_providers(config)
            for provider in providers:
                provider_tools = _initialize_provider_tools(provider)
                if provider_tools:
                    tools.extend(provider_tools)
                    for tool in provider_tools:
                        tool_registry.register("terraform", tool)
                        logger.info(f"✅ Registered tool: {tool.name}")

        # Initialize module tools if configured
        if config.get('terraform', {}).get('modules'):
            module_tools = initialize_module_tools(config)
            if module_tools:
                for tool in module_tools.values():
                    tools.append(tool)
                    tool_registry.register("terraform", tool)
                    logger.info(f"✅ Registered module tool: {tool.name}")

        return tools
    except Exception as e:
        logger.error(f"Failed to initialize tools: {str(e)}")
        return []

# Export all components
__all__ = [
    'initialize_tools',
    'TerraformModuleTool',
    'create_terraform_module_tool',
    'initialize_module_tools',
    'TerraformerTool'
]

# Initialize tools immediately
logger.info("🚀 Initializing Terraform tools...")
config = tool_registry.dynamic_config
if not config:
    logger.error("❌ No configuration found in tool registry")
    raise ValueError("No configuration found in tool registry")

tools = initialize_tools(config)
if not tools:
    logger.error("❌ No tools were initialized")
    raise ValueError("No tools were initialized")
logger.info(f"✅ Successfully initialized {len(tools)} tools")