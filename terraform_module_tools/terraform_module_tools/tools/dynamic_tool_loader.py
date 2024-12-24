from typing import List, Optional
from kubiya_sdk.tools import Tool
from kubiya_sdk.tools.registry import tool_registry
import logging
import os
import json
from .terraformer_tool import TerraformerTool, _initialize_provider_tools

logger = logging.getLogger(__name__)

def get_configured_providers() -> List[str]:
    """Get providers from configuration or environment."""
    try:
        # Try to get providers from environment variable
        config = tool_registry.dynamic_config
        if config is None:
            logger.info("No dynamic config found")
            return []
        
        # Check if terraform configuration exists and has providers specified
        terraform_config = config.get('terraform', {})
        if terraform_config.get('enable_reverse_terraform'):
            providers = terraform_config.get('reverse_terraform_providers', [])
            if providers:
                logger.info(f"Found configured providers: {providers}")
                return providers
    except Exception as e:
        logger.error(f"Failed to parse configuration: {str(e)}")
    
    return []

def load_tools() -> List[Tool]:
    """Load all available tools."""
    tools = []
    
    try:
        # Get configured providers
        providers = get_configured_providers()
        
        # If no providers configured, use AWS as default
        if not providers:
            logger.info("No providers configured, using AWS as default")
            providers = ['aws']
        
        # Initialize tools for each configured provider
        for provider in providers:
            provider_tools = _initialize_provider_tools(provider)
            if provider_tools:
                tools.extend(provider_tools)
                logger.info(f"Loaded {len(provider_tools)} tools for {provider}")
        
        if not tools:
            logger.warning("No tools were initialized")
        else:
            logger.info(f"Successfully loaded {len(tools)} tools in total")
            
    except Exception as e:
        logger.error(f"Failed to load tools: {str(e)}")
    
    return tools

def register_tools():
    """Register all tools with the tool registry."""
    try:
        tools = load_tools()
        if not tools:
            logger.warning("No tools to register")
            return
        
        registered_count = 0
        for tool in tools:
            try:
                tool_registry.register("terraform_module_tools", tool)
                logger.info(f"✅ Registered tool: {tool.name}")
                registered_count += 1
            except Exception as e:
                logger.error(f"Failed to register tool {tool.name}: {str(e)}")
        
        logger.info(f"Successfully registered {registered_count} tools")
        
    except Exception as e:
        logger.error(f"Failed to register tools: {str(e)}")
