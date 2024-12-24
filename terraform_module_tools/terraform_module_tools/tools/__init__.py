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
    
    logger.info(f"Starting tool initialization with config: {config}")
    
    # Always initialize terraformer tools for supported providers
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
try:
    logger.info("Getting configuration from registry")
    config = tool_registry.dynamic_config
    logger.info(f"Registry config: {config}")
    
    if not config:
        logger.info("No config found in registry, using default config")
        config = {'terraform': {'enable_reverse_terraform': True}}
    
    logger.info(f"Using configuration: {config}")
    tools = initialize_tools(config)
    
    if tools:
        logger.info(f"✅ Successfully initialized {len(tools)} tools")
        for tool in tools:
            logger.info(f"Tool available: {tool.name}")
    else:
        logger.warning("⚠️ No tools were initialized")
        logger.info("Checking tool registry state...")
        registered_tools = tool_registry.get_tools()
        logger.info(f"Tools in registry: {registered_tools}")
except Exception as e:
    logger.error(f"❌ Failed to initialize tools: {str(e)}", exc_info=True)