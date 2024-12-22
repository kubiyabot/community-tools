import os
import json
from typing import Dict, Any, List
from kubiya_sdk.tools import Tool
from kubiya_sdk.tools.registry import tool_registry
from . import create_terraform_module_tool
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)

class ModuleConfigError(Exception):
    """Custom exception for module configuration errors."""
    pass

def validate_module_config(module_name: str, module_config: Dict[str, Any]) -> None:
    """Validate module configuration and raise descriptive errors."""
    required_fields = ['name', 'description', 'source']
    missing_fields = [field for field in required_fields if field not in module_config]
    
    if missing_fields:
        raise ModuleConfigError(
            f"Module '{module_name}' is missing required fields: {', '.join(missing_fields)}"
        )

    # Validate source configuration
    source = module_config['source']
    if not isinstance(source, dict):
        raise ModuleConfigError(
            f"Module '{module_name}' has invalid source type. Expected dict, got {type(source)}"
        )
    
    # Check required source fields
    if 'location' not in source:
        raise ModuleConfigError(
            f"Module '{module_name}' source is missing required field 'location'"
        )

    # Validate auth if present
    if 'auth' in source:
        auth = source['auth']
        if not isinstance(auth, dict):
            raise ModuleConfigError(
                f"Module '{module_name}' has invalid auth type. Expected dict, got {type(auth)}"
            )
        
        if 'type' not in auth:
            raise ModuleConfigError(
                f"Module '{module_name}' auth is missing required field 'type'"
            )
        
        if auth['type'] not in ['ssh', 'https', 'token']:
            raise ModuleConfigError(
                f"Module '{module_name}' has invalid auth type. Expected one of: ssh, https, token"
            )
        
        if auth['type'] == 'ssh' and 'private_key_env' not in auth:
            raise ModuleConfigError(
                f"Module '{module_name}' SSH auth is missing required field 'private_key_env'"
            )
        
        if auth['type'] == 'token' and 'token_env' not in auth:
            raise ModuleConfigError(
                f"Module '{module_name}' token auth is missing required field 'token_env'"
            )
    
    # Validate variables if present
    if 'variables' in module_config:
        if not isinstance(module_config['variables'], dict):
            raise ModuleConfigError(
                f"Module '{module_name}' has invalid variables type. Expected dict, got {type(module_config['variables'])}"
            )
        
        for var_name, var_config in module_config['variables'].items():
            if not isinstance(var_config, dict):
                raise ModuleConfigError(
                    f"Module '{module_name}' variable '{var_name}' has invalid configuration type. Expected dict, got {type(var_config)}"
                )
            
            if 'type' not in var_config:
                raise ModuleConfigError(
                    f"Module '{module_name}' variable '{var_name}' is missing required field 'type'"
                )

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
        
        # Create module configuration
        config = {
            'name': module_name,
            'description': module_config.get('description', f"Terraform module for {module_name}"),
            'source': {
                'location': module_config['source']['location'],
                'version': module_config['source'].get('version'),
                'path': module_config['source'].get('path'),
                'auth': module_config['source'].get('auth')
            },
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

# Export the loader function and error class
__all__ = ['load_terraform_tools', 'ModuleConfigError']