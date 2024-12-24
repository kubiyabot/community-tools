import os
import json
from typing import Dict, Any, List
from kubiya_sdk.tools import Tool
from kubiya_sdk.tools.registry import tool_registry
from terraform_module_tools.tools.module_tools import create_terraform_module_tool
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)

def validate_module_config(module_name: str, module_config: Dict[str, Any]) -> None:
    """Validate module configuration."""
    # Check for required source field
    if 'source' not in module_config:
        raise ValueError(f"Module '{module_name}' is missing required field 'source'")

    # Validate source format
    source = module_config['source']
    if not isinstance(source, str) and not isinstance(source, dict):
        raise ValueError(f"Module '{module_name}' has invalid source type. Expected string or dict")

    # If source is a dict, validate its structure
    if isinstance(source, dict):
        if 'location' not in source:
            raise ValueError(f"Module '{module_name}' source is missing required field 'location'")

        # Validate auth if present
        if 'auth' in source:
            auth = source['auth']
            if not isinstance(auth, dict):
                raise ValueError(f"Module '{module_name}' has invalid auth type")
            
            if 'type' not in auth:
                raise ValueError(f"Module '{module_name}' auth is missing required field 'type'")
            
            if auth['type'] not in ['ssh', 'https', 'token']:
                raise ValueError(f"Module '{module_name}' has invalid auth type")

    # Validate variables if present and auto_discover is false
    if not module_config.get('auto_discover', True) and 'variables' in module_config:
        if not isinstance(module_config['variables'], dict):
            raise ValueError(f"Module '{module_name}' has invalid variables type")
        
        for var_name, var_config in module_config['variables'].items():
            if not isinstance(var_config, dict):
                raise ValueError(f"Module '{module_name}' variable '{var_name}' has invalid configuration")
            
            if 'type' not in var_config:
                raise ValueError(f"Module '{module_name}' variable '{var_name}' is missing required field 'type'")

def load_terraform_tools():
    """Load and register all Terraform tools from dynamic configuration."""
    tools = []
    
    try:
        # Get dynamic configuration from tool registry
        dynamic_config = getattr(tool_registry, 'dynamic_config', None)
        if not dynamic_config:
            logger.warning("No dynamic configuration found in tool registry")
            return tools

        # Get terraform modules configuration
        tf_modules = dynamic_config.get('tf_modules') or dynamic_config.get('terraform_modules')
        if not tf_modules:
            logger.warning("No terraform modules found in dynamic configuration")
            return tools

        logger.info(f"Found {len(tf_modules)} modules in configuration")

        # Process modules in parallel
        with ThreadPoolExecutor(max_workers=min(len(tf_modules), 4)) as executor:
            future_to_module = {
                executor.submit(_process_module, module_name, module_config): module_name
                for module_name, module_config in tf_modules.items()
            }

            for future in as_completed(future_to_module):
                module_name = future_to_module[future]
                try:
                    module_tools = future.result()
                    if module_tools:
                        tools.extend(module_tools)
                        logger.info(f"✅ Successfully processed module: {module_name}")
                except Exception as e:
                    logger.error(f"❌ Failed to process module {module_name}: {str(e)}")

        if tools:
            logger.info(f"✅ Successfully loaded {len(tools)} tools")
        else:
            logger.warning("⚠️ No tools were created")

    except Exception as e:
        logger.error(f"❌ Failed to load tools: {str(e)}", exc_info=True)

    return tools

def _process_module(module_name: str, module_config: Dict[str, Any]) -> List[Tool]:
    """Process a single module in parallel."""
    module_tools = []
    try:
        logger.info(f"📦 Processing module: {module_name}")
        
        # Validate module configuration
        validate_module_config(module_name, module_config)
        
        # Normalize source configuration
        source_config = module_config['source']
        if isinstance(source_config, str):
            source_config = {
                'location': source_config,
                'version': module_config.get('version')
            }
        
        # Create module configuration
        config = {
            'name': module_name,
            'description': module_config.get('description', f"Terraform module for {module_name}"),
            'source': source_config,
            'auto_discover': module_config.get('auto_discover', True),
            'instructions': module_config.get('instructions'),
            'variables': module_config.get('variables', {})
        }
        
        # Create tools for this module
        for action in ['plan', 'apply']:
            tool = create_terraform_module_tool(config, action)
            if tool:
                module_tools.append(tool)
                tool_registry.register("terraform", tool)
                logger.info(f"✅ Created {action} tool for {module_name}")
            else:
                logger.warning(f"⚠️ Failed to create {action} tool for {module_name}")
                
    except Exception as e:
        logger.error(f"❌ Failed to process module {module_name}: {str(e)}", exc_info=True)
        
    return module_tools

