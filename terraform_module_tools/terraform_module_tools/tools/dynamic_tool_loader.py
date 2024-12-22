import os
import json
from typing import Dict, Any, List
from kubiya_sdk.tools import Arg
from kubiya_sdk.tools.registry import tool_registry
from ..parser import TerraformModuleParser
from . import create_terraform_module_tool
import logging

logger = logging.getLogger(__name__)

class ModuleConfigError(Exception):
    """Custom exception for module configuration errors."""
    pass

def validate_module_config(module_name: str, module_config: Dict[str, Any]) -> None:
    """Validate module configuration and raise descriptive errors."""
    required_fields = ['source']
    missing_fields = [field for field in required_fields if field not in module_config]
    
    if missing_fields:
        raise ModuleConfigError(
            f"Module '{module_name}' is missing required fields: {', '.join(missing_fields)}"
        )

    # Validate source format
    source = module_config['source']
    if not isinstance(source, str):
        raise ModuleConfigError(
            f"Module '{module_name}' has invalid source type. Expected string, got {type(source)}"
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

        if not isinstance(tf_modules, dict):
            raise ModuleConfigError(
                f"Invalid terraform modules configuration type. Expected dict, got {type(tf_modules)}"
            )

        logger.info(f"Found {len(tf_modules)} modules in configuration")

        # Process each module
        for module_name, module_config in tf_modules.items():
            try:
                logger.info(f"📦 Loading module: {module_name}")
                
                # Validate module configuration
                validate_module_config(module_name, module_config)
                
                # Create module configuration
                config = {
                    'name': module_name,
                    'source': {
                        'location': module_config['source'],
                        'version': module_config.get('version')
                    },
                    'auto_discover': module_config.get('auto_discover', True),
                    'instructions': module_config.get('instructions'),
                    'variables': module_config.get('variables', {})
                }
                
                # Create tools for this module
                for action in ['plan', 'apply']:
                    tool = create_terraform_module_tool(config, action)
                    if tool:
                        tools.append(tool)
                        tool_registry.register("terraform", tool)
                        logger.info(f"✅ Created {action} tool for {module_name}")
                    else:
                        logger.warning(f"⚠️ Failed to create {action} tool for {module_name}")
                    
            except ModuleConfigError as e:
                logger.error(f"❌ Invalid configuration for module {module_name}: {str(e)}")
                continue
            except Exception as e:
                logger.error(f"❌ Failed to process module {module_name}: {str(e)}", exc_info=True)
                continue

        if tools:
            logger.info(f"✅ Successfully loaded {len(tools)} tools")
        else:
            logger.warning("⚠️ No tools were created")

    except ModuleConfigError as e:
        logger.error(f"❌ Configuration error: {str(e)}")
    except Exception as e:
        logger.error(f"❌ Failed to load tools: {str(e)}", exc_info=True)

    return tools

# Export the loader function and error class
__all__ = ['load_terraform_tools', 'ModuleConfigError']