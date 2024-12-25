from typing import List, Dict, Any
from kubiya_sdk.tools import Tool
from kubiya_sdk.tools.registry import tool_registry
import logging
from .terraformer_tool import TerraformerTool, _initialize_provider_tools
from .module_tools import initialize_module_tools

logger = logging.getLogger(__name__)

def initialize_tools(config: Dict[str, Any]) -> List[Tool]:
    """Initialize all Terraform tools from configuration."""
    tools = []
    
    logger.info(f"Starting tool initialization with config: {config}")
    
    # Initialize terraformer tools if enabled
    terraform_config = config.get('terraform', {})
    logger.info(f"Terraform config section: {terraform_config}")
    
    if terraform_config.get('enable_reverse_terraform'):
        logger.info("🔄 Loading reverse terraform tools...")
        providers = terraform_config.get('reverse_terraform_providers', ['aws', 'gcp', 'azure'])
        logger.info(f"Initializing for providers: {providers}")
        
        for provider in providers:
            logger.info(f"Processing provider: {provider}")
            if provider not in TerraformerTool.SUPPORTED_PROVIDERS:
                logger.warning(f"⚠️ Unsupported provider: {provider}")
                continue
            
            logger.info(f"Initializing tools for provider: {provider}")
            provider_tools = _initialize_provider_tools(provider)
            if provider_tools:
                for tool in provider_tools:
                    logger.info(f"Adding tool: {tool.name}")
                    tools.append(tool)
                    tool_registry.register("terraform", tool)
                    logger.info(f"✅ Registered reverse terraform tool: {tool.name}")
            else:
                logger.warning(f"No tools initialized for provider: {provider}")

    # Initialize module tools if configured
    if terraform_config.get('modules'):
        logger.info("📦 Loading module tools...")
        try:
            logger.info("Attempting to initialize module tools")
            module_tools = initialize_module_tools(config)
            if module_tools:
                for tool in module_tools.values():
                    logger.info(f"Adding module tool: {tool.name}")
                    tools.append(tool)
                    tool_registry.register("terraform", tool)
                    logger.info(f"✅ Registered module tool: {tool.name}")
        except Exception as e:
            logger.warning(f"Failed to initialize module tools: {str(e)}", exc_info=True)

    logger.info(f"Initialization complete. Total tools created: {len(tools)}")
    for tool in tools:
        logger.info(f"Initialized tool: {tool.name} ({type(tool).__name__})")
    
    return tools

__all__ = ['initialize_tools']

