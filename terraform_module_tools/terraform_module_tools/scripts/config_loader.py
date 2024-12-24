import logging
from typing import Dict, Any, Optional, List, Tuple
import json
import os
from kubiya_sdk.tools.registry import tool_registry

logger = logging.getLogger(__name__)

class ConfigurationError(Exception):
    """Exception raised for configuration errors."""
    pass

def validate_module_config(module_name: str, config: Dict[str, Any]) -> None:
    """Validate module configuration."""
    required_fields = ['source']
    optional_fields = ['version', 'description', 'variables', 'auto_discover']
    
    # Check required fields
    missing_fields = [field for field in required_fields if field not in config]
    if missing_fields:
        raise ConfigurationError(
            f"Module '{module_name}' is missing required fields: {', '.join(missing_fields)}"
        )
    
    # Add default description if not provided
    if 'description' not in config:
        logger.warning(f"Module '{module_name}' is missing description. Using default.")
        config['description'] = f"Terraform module for {module_name}"

def validate_reverse_terraform_config(config: Dict[str, Any]) -> None:
    """Validate reverse terraform configuration."""
    if config.get('enable_reverse_terraform'):
        providers = config.get('reverse_terraform_providers')
        if not providers:
            raise ConfigurationError(
                "When enable_reverse_terraform is true, reverse_terraform_providers must be specified"
            )
        if not isinstance(providers, (list, str)):
            raise ConfigurationError(
                "reverse_terraform_providers must be a string or list of strings"
            )

def merge_configs(file_config: Optional[Dict[str, Any]], 
                 dynamic_config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Merge file-based and dynamic configurations."""
    config = {
        'terraform': {
            'modules': {},
            'enable_reverse_terraform': False,
            'reverse_terraform_providers': []
        }
    }
    
    # Merge file config if present
    if file_config and 'terraform' in file_config:
        config['terraform'].update(file_config['terraform'])
    
    # Merge dynamic config if present
    if dynamic_config:
        # Handle legacy tf_modules format
        if 'tf_modules' in dynamic_config:
            for module_name, module_config in dynamic_config['tf_modules'].items():
                config['terraform']['modules'][module_name] = module_config
                
        # Handle new terraform section format
        if 'terraform' in dynamic_config:
            terraform_config = dynamic_config['terraform']
            
            # Merge modules
            if 'modules' in terraform_config:
                config['terraform']['modules'].update(terraform_config['modules'])
            
            # Merge reverse terraform settings
            if 'enable_reverse_terraform' in terraform_config:
                config['terraform']['enable_reverse_terraform'] = (
                    terraform_config['enable_reverse_terraform']
                )
            if 'reverse_terraform_providers' in terraform_config:
                config['terraform']['reverse_terraform_providers'] = (
                    terraform_config['reverse_terraform_providers']
                )
    
    return config

def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Load and validate configuration from file and dynamic config."""
    try:
        # Load file configuration
        file_config = None
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                file_config = json.load(f)
        
        # Get dynamic configuration
        dynamic_config = getattr(tool_registry, 'dynamic_config', None)
        
        # Merge configurations
        config = merge_configs(file_config, dynamic_config)
        
        # Validate terraform section
        if 'terraform' not in config:
            raise ConfigurationError("Missing 'terraform' section in configuration")
            
        terraform_config = config['terraform']
        
        # Validate modules if present
        if 'modules' in terraform_config:
            modules = terraform_config['modules']
            if not isinstance(modules, dict):
                raise ConfigurationError("'modules' must be a dictionary")
                
            # Validate each module
            for module_name, module_config in modules.items():
                try:
                    validate_module_config(module_name, module_config)
                except ConfigurationError as e:
                    logger.error(f"Invalid configuration for module '{module_name}': {str(e)}")
                    raise
        
        # Validate reverse terraform configuration
        validate_reverse_terraform_config(terraform_config)
        
        # Ensure at least one feature is enabled
        if not terraform_config.get('modules') and not terraform_config.get('enable_reverse_terraform'):
            raise ConfigurationError(
                "Configuration must include at least one module or enable reverse terraform"
            )
                
        return config
        
    except json.JSONDecodeError as e:
        error_msg = f"Failed to parse configuration file: {str(e)}"
        logger.error(error_msg)
        raise ConfigurationError(error_msg)
        
    except Exception as e:
        error_msg = f"Failed to load module configurations: {str(e)}"
        logger.error(error_msg)
        raise ConfigurationError(error_msg)

def get_enabled_features(config: Dict[str, Any]) -> Tuple[bool, bool]:
    """Get which features are enabled in the configuration."""
    terraform_config = config.get('terraform', {})
    has_modules = bool(terraform_config.get('modules'))
    reverse_terraform_enabled = terraform_config.get('enable_reverse_terraform', False)
    return has_modules, reverse_terraform_enabled

def get_module_configs(config: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    Extract and validate module configurations from the main config.
    
    Args:
        config: The full configuration dictionary
        
    Returns:
        Dict[str, Dict[str, Any]]: Dictionary of validated module configurations
        
    Raises:
        ConfigurationError: If module configurations are invalid
    """
    try:
        terraform_config = config.get('terraform', {})
        
        # Handle both new and legacy formats
        modules = {}
        
        # Handle new format (terraform.modules)
        if 'modules' in terraform_config:
            modules.update(terraform_config['modules'])
            
        # Handle legacy format (tf_modules)
        if 'tf_modules' in config:
            modules.update(config['tf_modules'])
            
        # Validate each module configuration
        validated_modules = {}
        for module_name, module_config in modules.items():
            try:
                # Validate the module configuration
                validate_module_config(module_name, module_config)
                
                # Add validated configuration
                validated_modules[module_name] = {
                    'source': module_config['source'],
                    'version': module_config.get('version'),
                    'description': module_config.get('description', f"Terraform module for {module_name}"),
                    'variables': module_config.get('variables', {}),
                    'auto_discover': module_config.get('auto_discover', True)
                }
                
            except Exception as e:
                logger.error(f"Failed to validate module '{module_name}': {str(e)}")
                raise ConfigurationError(f"Invalid configuration for module '{module_name}': {str(e)}")
                
        return validated_modules
        
    except Exception as e:
        error_msg = f"Failed to process module configurations: {str(e)}"
        logger.error(error_msg)
        raise ConfigurationError(error_msg)

def get_reverse_terraform_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract and validate reverse terraform configuration.
    
    Args:
        config: The full configuration dictionary
        
    Returns:
        Dict[str, Any]: Dictionary containing reverse terraform configuration
        
    Raises:
        ConfigurationError: If reverse terraform configuration is invalid
    """
    try:
        terraform_config = config.get('terraform', {})
        
        # Check if reverse terraform is enabled
        if not terraform_config.get('enable_reverse_terraform'):
            return {
                'enabled': False,
                'providers': []
            }
            
        # Get and validate providers
        providers = terraform_config.get('reverse_terraform_providers', [])
        if isinstance(providers, str):
            providers = [providers]
            
        if not providers:
            raise ConfigurationError(
                "When enable_reverse_terraform is true, reverse_terraform_providers must be specified"
            )
            
        return {
            'enabled': True,
            'providers': providers
        }
        
    except Exception as e:
        error_msg = f"Failed to process reverse terraform configuration: {str(e)}"
        logger.error(error_msg)
        raise ConfigurationError(error_msg)

__all__ = [
    'load_config',
    'ConfigurationError',
    'get_enabled_features',
    'get_module_configs',
    'get_reverse_terraform_config'
]
