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
        terraform_config = config.get('terraform', {})
        if not terraform_config:
            logger.warning("No terraform configuration found")
            return tools

        # Initialize terraformer tools if enabled
        if terraform_config.get('enable_reverse_terraform'):
            logger.info("🔄 Loading reverse terraform tools...")
            providers = terraform_config.get('reverse_terraform_providers', [])
            if not providers:
                logger.warning("No providers specified for reverse terraform")
            else:
                for provider in providers:
                    if provider not in TerraformerTool.SUPPORTED_PROVIDERS:
                        logger.warning(f"⚠️ Unsupported provider: {provider}")
                        continue
                    
                    provider_tools = _initialize_provider_tools(provider)
                    if provider_tools:
                        tools.extend(provider_tools)
                        for tool in provider_tools:
                            tool_registry.register("terraform", tool)
                            logger.info(f"✅ Registered reverse terraform tool: {tool.name}")
                    else:
                        logger.warning(f"No tools initialized for provider: {provider}")

        # Initialize module tools if configured
        if terraform_config.get('modules'):
            logger.info("📦 Loading module tools...")
            module_tools = initialize_module_tools(config)
            if module_tools:
                for tool in module_tools.values():
                    tools.append(tool)
                    tool_registry.register("terraform", tool)
                    logger.info(f"✅ Registered module tool: {tool.name}")
            else:
                logger.warning("No module tools were initialized")

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
    logger.error("❌ No configuration found, please check your configuration and try again")
    raise ValueError("No configuration found, please check your configuration and try again")

try:
    tools = initialize_tools(config)
    if not tools:
        logger.error("❌ No tools were initialized")
        raise ValueError("Could not initialize tools from the given configuration, please check your configuration and try again")
    logger.info(f"✅ Successfully initialized {len(tools)} tools")
except Exception as e:
    logger.error(f"Failed to initialize tools: {str(e)}")
    raise ValueError(f"Failed to initialize tools from the given configuration: {str(e)}")