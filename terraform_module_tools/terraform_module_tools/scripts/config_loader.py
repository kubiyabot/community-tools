import json
import logging
from pathlib import Path
from typing import Dict, Any
import os
import subprocess
import tempfile
import glob

logger = logging.getLogger(__name__)

# Try to import jsonschema, but don't fail if it's not available
try:
    from jsonschema import validate
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    logger.warning("jsonschema not available - validation will be skipped")
    JSONSCHEMA_AVAILABLE = False

# JSON Schema for validation
MODULE_CONFIG_SCHEMA = {
    "type": "object",
    "patternProperties": {
        ".*": {
            "type": "object",
            "required": ["name", "description", "source"],
            "properties": {
                "name": {"type": "string"},
                "description": {"type": "string"},
                "source": {
                    "type": "object",
                    "required": ["location"],
                    "properties": {
                        "location": {"type": "string"},
                        "version": {"type": "string"},
                        "path": {"type": "string"},
                        "auth": {
                            "type": "object",
                            "properties": {
                                "type": {
                                    "type": "string",
                                    "enum": ["ssh", "https", "token"]
                                },
                                "private_key_env": {"type": "string"},
                                "token_env": {"type": "string"}
                            }
                        }
                    }
                },
                "pre_script": {"type": "string"}
            }
        }
    }
}

def detect_source_type(location: str) -> str:
    """Detect the type of source from its location."""
    if location.startswith(('http://', 'https://', 'git@')):
        return 'git'
    elif '/' in location and not location.startswith('/'):
        return 'registry'
    else:
        return 'local'

def validate_module_path(source: dict) -> bool:
    """Validate that the module path exists and contains valid Terraform files."""
    location = source['location']
    path = source.get('path')
    
    if detect_source_type(location) == 'git':
        # Clone repository to temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                # Clone repo
                if location.startswith('git@'):
                    # Handle SSH auth
                    if 'auth' in source and source['auth']['type'] == 'ssh':
                        # Set up SSH key
                        key_env = source['auth']['private_key_env']
                        if key_env not in os.environ:
                            raise ValueError(f"SSH key environment variable {key_env} not set")
                        # Clone with SSH
                        subprocess.run(['git', 'clone', location, temp_dir], check=True)
                else:
                    # Clone with HTTPS
                    subprocess.run(['git', 'clone', location, temp_dir], check=True)
                
                # Checkout specific version if specified
                if 'version' in source:
                    subprocess.run(['git', 'checkout', source['version']], cwd=temp_dir, check=True)
                
                # Check module path
                module_path = os.path.join(temp_dir, path) if path else temp_dir
                return _validate_terraform_files(module_path)
                
            except subprocess.CalledProcessError as e:
                raise ValueError(f"Git operation failed: {str(e)}")
    else:
        # For local paths, check directly
        module_path = os.path.join(location, path) if path else location
        return _validate_terraform_files(module_path)

def _validate_terraform_files(path: str) -> bool:
    """Check if directory contains valid Terraform files."""
    if not os.path.isdir(path):
        raise ValueError(f"Module path not found: {path}")
    
    # Check for Terraform files
    tf_files = glob.glob(os.path.join(path, '*.tf'))
    if not tf_files:
        raise ValueError(f"No Terraform files found in {path}")
    
    # Check for multiple modules
    module_dirs = [d for d in os.listdir(path) 
                  if os.path.isdir(os.path.join(path, d)) and 
                  glob.glob(os.path.join(path, d, '*.tf'))]
    
    if module_dirs:
        if not path.endswith(('modules', 'examples')):
            raise ValueError(
                f"Multiple modules found in {path}. Please specify a specific module path using 'path' parameter. "
                f"Available modules: {', '.join(module_dirs)}"
            )
    
    return True

def validate_config(config: Dict[str, Any]) -> bool:
    """Validate configuration with fallback for missing jsonschema."""
    if not JSONSCHEMA_AVAILABLE:
        # Basic validation without jsonschema
        for module_name, module_config in config.items():
            required_fields = ["name", "description", "source"]
            for field in required_fields:
                if field not in module_config:
                    raise ValueError(f"Missing required field '{field}' in module '{module_name}'")
            
            if not isinstance(module_config["source"], dict):
                raise ValueError(f"'source' must be an object in module '{module_name}'")
            
            if "location" not in module_config["source"]:
                raise ValueError(f"Missing required field 'location' in source of module '{module_name}'")
        return True
    else:
        validate(instance=config, schema=MODULE_CONFIG_SCHEMA)
        return True

def get_module_configs() -> Dict[str, Any]:
    """Get Terraform module configurations."""
    try:
        config_path = Path(__file__).parent / 'configs' / 'module_configs.json'
        if not config_path.exists():
            logger.warning(f"No module configurations found at {config_path}")
            return {}

        with open(config_path) as f:
            configs = json.load(f)

        # Validate configuration
        validate_config(configs)
        
        # Validate each module source
        for module_name, config in configs.items():
            try:
                validate_module_path(config['source'])
            except ValueError as e:
                logger.error(f"Invalid module source for {module_name}: {str(e)}")
                continue
        
        return configs

    except Exception as e:
        logger.error(f"Failed to load module configurations: {str(e)}")
        return {} 