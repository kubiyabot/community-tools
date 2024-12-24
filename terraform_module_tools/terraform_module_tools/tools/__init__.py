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

        terraform_config = config.get('terraform', {})
        
        # Initialize reverse terraform tools if enabled
        if terraform_config.get('enable_reverse_terraform'):
            logger.info("Initializing reverse Terraform engineering tools")
            providers = terraform_config.get('reverse_terraform_providers', [])
            if not providers:
                logger.error("No providers specified for reverse Terraform engineering")
            else:
                logger.info(f"Initializing tools for providers: {providers}")
                for provider in providers:
                    try:
                        provider_tools = _initialize_provider_tools(provider, tool_registry)
                        if provider_tools:
                            tools.extend(provider_tools)
                            for tool in provider_tools:
                                tool_registry.register("terraform", tool)
                            logger.info(f"✅ Successfully initialized tools for provider: {provider}")
                        else:
                            logger.warning(f"⚠️ No tools created for provider: {provider}")
                    except Exception as e:
                        logger.error(f"❌ Failed to initialize tools for provider {provider}: {str(e)}")

        # Initialize module tools if modules are configured
        if terraform_config.get('modules'):
            logger.info("Initializing Terraform module tools")
            module_tools = initialize_module_tools(config)
            if module_tools:
                tools.extend(module_tools.values())
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

# Update TerraformerTool to better handle provider validation
class TerraformerTool(Tool):
    @classmethod
    def get_enabled_providers(cls, config: Dict[str, Any]) -> List[str]:
        """Get list of enabled providers from configuration."""
        if 'terraform' not in config and any(
            key in config for key in ['enable_reverse_terraform', 'reverse_terraform_providers']
        ):
            config = {'terraform': config}
            
        terraform_config = config.get('terraform', {})
        if not terraform_config.get('enable_reverse_terraform'):
            return []
            
        providers = terraform_config.get('reverse_terraform_providers', [])
        if isinstance(providers, str):
            providers = [providers]
            
        if not providers:
            logger.warning("Reverse Terraform engineering is enabled but no providers specified")
            return []
            
        # Validate providers
        valid_providers = []
        for provider in providers:
            if provider in cls.SUPPORTED_PROVIDERS:
                valid_providers.append(provider)
            else:
                logger.warning(f"Unsupported provider: {provider}. Supported providers: {list(cls.SUPPORTED_PROVIDERS.keys())}")
                
        return valid_providers
