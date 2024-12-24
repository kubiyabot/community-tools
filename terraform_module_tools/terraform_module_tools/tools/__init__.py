import logging
from typing import List, Any, Dict, Optional
from kubiya_sdk.tools import Tool
from kubiya_sdk.tools.registry import tool_registry
from .terraform_module_tool import TerraformModuleTool
from .terraformer_tool import TerraformerTool, _initialize_provider_tools
from .module_tools import create_terraform_module_tool, initialize_module_tools
from ..parser import TerraformModuleParser
from ..scripts.config_loader import ConfigurationError
import re

logger = logging.getLogger(__name__)

def initialize_tools(config: Dict[str, Any]) -> List[Tool]:
    """Initialize all Terraform tools from configuration."""
    tools = []
    try:
        if not config:
            raise ConfigurationError("No configuration provided")

        # If config is not under 'terraform' key but has relevant keys, wrap it
        if 'terraform' not in config and any(
            key in config for key in [
                'enable_reverse_terraform',
                'reverse_terraform_providers',
                'modules',
                'tf_modules'
            ]
        ):
            config = {'terraform': config}
            logger.info("Wrapped configuration under 'terraform' key")

        terraform_config = config.get('terraform', {})
        logger.info(f"Processing terraform configuration: {terraform_config}")
        
        # Initialize reverse terraform tools if enabled
        if terraform_config.get('enable_reverse_terraform'):
            logger.info("🔄 Initializing reverse Terraform engineering tools")
            providers = terraform_config.get('reverse_terraform_providers', [])
            if not providers:
                logger.error("❌ No providers specified for reverse Terraform engineering")
            else:
                logger.info(f"Found providers: {providers}")
                for provider in providers:
                    try:
                        provider_tools = _initialize_provider_tools(provider)
                        if provider_tools:
                            tools.extend(provider_tools)
                            for tool in provider_tools:
                                tool_registry.register("terraform", tool)
                                logger.info(f"✅ Registered tool: {tool.name}")
                            logger.info(f"✅ Successfully initialized tools for provider: {provider}")
                        else:
                            logger.warning(f"⚠️ No tools created for provider: {provider}")
                    except Exception as e:
                        logger.error(f"❌ Failed to initialize tools for provider {provider}: {str(e)}")

        # Initialize module tools if modules are configured
        if terraform_config.get('modules'):
            logger.info("📦 Initializing Terraform module tools")
            module_tools = initialize_module_tools(config)
            if module_tools:
                for tool in module_tools.values():
                    tools.append(tool)
                    tool_registry.register("terraform", tool)
                    logger.info(f"✅ Registered module tool: {tool.name}")
                logger.info(f"✅ Successfully initialized {len(module_tools)} module tools")
            else:
                logger.warning("⚠️ No module tools were created")

        if not tools:
            logger.warning(
                "⚠️ No tools were created. Make sure either 'enable_reverse_terraform' is true with providers "
                "or 'modules' is configured properly."
            )
            return []

        logger.info(f"🎉 Successfully initialized {len(tools)} total tools")
        return tools
        
    except ConfigurationError as e:
        logger.error(f"Configuration error: {str(e)}")
        raise
    except Exception as e:
        error_msg = f"Failed to initialize tools: {str(e)}"
        logger.error(error_msg)
        raise ConfigurationError(error_msg)

# Export all necessary components
__all__ = [
    'initialize_tools',
    'create_terraform_module_tool',
    'initialize_module_tools',
    'TerraformModuleTool',
    'TerraformerTool'
]

# Re-export the functions at the module level
from .module_tools import create_terraform_module_tool, initialize_module_tool

config = tool_registry.dynamic_config
if not config:
    logger.warning("⚠️ No dynamic configuration found. Terraform tools will not be initialized.")
    raise ConfigurationError("No dynamic configuration found. Terraform tools will not be initialized.")
initialize_tools(config)