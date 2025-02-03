import logging
from typing import Dict, Any, Optional, List, Tuple, Union
import json
import os
from kubiya_sdk.tools.registry import tool_registry

logger = logging.getLogger(__name__)

class ConfigurationError(Exception):
    """Exception raised for configuration errors."""
    def __init__(self, message: str, expected_structure: Optional[Dict[str, Any]] = None):
        self.message = message
        self.expected_structure = expected_structure
        super().__init__(self.get_formatted_message())
        
    def get_formatted_message(self) -> str:
        """Format error message with expected structure if available."""
        msg = f"Configuration Error: {self.message}"
        if self.expected_structure:
            msg += "\n\nExpected structure:"
            msg += json.dumps(self.expected_structure, indent=2)
        return msg

def validate_module_config(module_name: str, config: Union[Dict[str, Any], Any]) -> None:
    """Validate module configuration."""
    # First check if config is a dictionary
    if not isinstance(config, dict):
        raise ConfigurationError(
            f"Module '{module_name}' configuration must be a dictionary, got {type(config)}",
            expected_structure={
                "source": "module-source",  # Required
                "version": "module-version",  # Optional
                "description": "module-description",  # Optional
                "variables": {},  # Optional
                "auto_discover": True  # Optional
            }
        )
    
    required_fields = ['source']
    optional_fields = ['version', 'description', 'variables', 'auto_discover']
    
    # Check required fields
    missing_fields = [field for field in required_fields if field not in config]
    if missing_fields:
        raise ConfigurationError(
            f"Module '{module_name}' is missing required fields: {', '.join(missing_fields)}",
            expected_structure={
                field: "required" for field in missing_fields
            }
        )
    
    # Validate variables if present
    if 'variables' in config and not isinstance(config['variables'], dict):
        raise ConfigurationError(
            f"Module '{module_name}': 'variables' must be a dictionary",
            expected_structure={
                "variables": {
                    "variable_name": "variable_value",
                    "another_variable": "another_value"
                }
            }
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
                "When enable_reverse_terraform is true, reverse_terraform_providers must be specified",
                expected_structure={
                    "terraform": {
                        "enable_reverse_terraform": True,
                        "reverse_terraform_providers": ["aws", "gcp", "azure"]
                    }
                }
            )
        if not isinstance(providers, (list, str)):
            raise ConfigurationError(
                "reverse_terraform_providers must be a string or list of strings",
                expected_structure={
                    "terraform": {
                        "enable_reverse_terraform": True,
                        "reverse_terraform_providers": ["aws", "gcp", "azure"]
                    }
                }
            )

def merge_configs(file_config: Optional[Dict[str, Any]], 
                 dynamic_config: Optional[Dict[str, Any]],
                 input_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Merge file-based, dynamic, and input configurations."""
    config = {
        'terraform': {
            'modules': {},
            'enable_reverse_terraform': False,
            'reverse_terraform_providers': []
        }
    }
    
    # Helper function to merge terraform config
    def merge_terraform_section(source_config):
        if not source_config:
            return
            
        # If config is not under 'terraform' key but has relevant keys, treat it as terraform config
        if 'terraform' not in source_config and any(
            key in source_config for key in [
                'enable_reverse_terraform',
                'reverse_terraform_providers',
                'modules',
                'tf_modules'
            ]
        ):
            terraform_section = source_config
        else:
            terraform_section = source_config.get('terraform', {})
            
        # Merge modules
        if 'modules' in terraform_section:
            config['terraform']['modules'].update(terraform_section['modules'])
            
        # Handle legacy tf_modules format
        if 'tf_modules' in source_config:
            for module_name, module_config in source_config['tf_modules'].items():
                config['terraform']['modules'][module_name] = module_config
                
        # Merge reverse terraform settings
        if 'enable_reverse_terraform' in terraform_section:
            config['terraform']['enable_reverse_terraform'] = (
                terraform_section['enable_reverse_terraform']
            )
        if 'reverse_terraform_providers' in terraform_section:
            config['terraform']['reverse_terraform_providers'] = (
                terraform_section['reverse_terraform_providers']
            )
    
    # Merge configurations in order of precedence
    merge_terraform_section(file_config)
    merge_terraform_section(dynamic_config)
    merge_terraform_section(input_config)  # Input config takes highest precedence
    
    return config

def load_config(config_path: Optional[str] = None, input_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Load and validate configuration from file, dynamic config, and input config."""
    try:
        # Load file configuration
        file_config = None
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                file_config = json.load(f)
        
        # Get dynamic configuration
        dynamic_config = getattr(tool_registry, 'dynamic_config', None)
        
        # Merge configurations
        config = merge_configs(file_config, dynamic_config, input_config)
        
        # Validate the merged configuration
        validate_config(config)
        
        return config
        
    except json.JSONDecodeError as e:
        raise ConfigurationError(
            f"Failed to parse configuration file: {str(e)}. File must be valid JSON.",
            expected_structure={
                "terraform": {
                    "modules": {},
                    "enable_reverse_terraform": False,
                    "reverse_terraform_providers": []
                }
            }
        )
        
    except Exception as e:
        if isinstance(e, ConfigurationError):
            raise
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

def validate_config(config: Dict[str, Any]) -> None:
    """Validate the complete configuration structure."""
    # Validate terraform section
    if 'terraform' not in config:
        raise ConfigurationError(
            "Missing 'terraform' section in configuration",
            expected_structure={
                "terraform": {
                    "modules": {
                        "module_name": {
                            "source": "module-source",
                            "version": "module-version",
                            "description": "module-description",
                            "variables": {}
                        }
                    },
                    "enable_reverse_terraform": True,
                    "reverse_terraform_providers": ["aws", "gcp", "azure"]
                }
            }
        )
        
    terraform_config = config['terraform']
    
    # Validate modules if present
    if 'modules' in terraform_config:
        modules = terraform_config['modules']
        if not isinstance(modules, dict):
            raise ConfigurationError(
                "'modules' must be a dictionary",
                expected_structure={
                    "terraform": {
                        "modules": {
                            "module_name": {
                                "source": "module-source",
                                "version": "module-version"
                            }
                        }
                    }
                }
            )
            
        # Validate each module
        for module_name, module_config in modules.items():
            validate_module_config(module_name, module_config)
    
    # Validate reverse terraform configuration
    validate_reverse_terraform_config(terraform_config)
    
    # Ensure at least one feature is enabled
    if not terraform_config.get('modules') and not terraform_config.get('enable_reverse_terraform'):
        raise ConfigurationError(
            "Configuration must include at least one module or enable reverse terraform",
            expected_structure={
                "terraform": {
                    "modules": {
                        "module_name": {
                            "source": "module-source"
                        }
                    },
                    # OR
                    "enable_reverse_terraform": True,
                    "reverse_terraform_providers": ["aws"]
                }
            }
        )

__all__ = [
    'load_config',
    'ConfigurationError',
    'get_enabled_features',
    'get_module_configs',
    'get_reverse_terraform_config'
]
