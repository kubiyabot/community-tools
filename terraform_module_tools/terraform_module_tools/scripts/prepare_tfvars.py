#!/usr/bin/env python3
import os
import sys
import json
from pathlib import Path
from typing import Dict, Any
from terraform_tools.error_handler import handle_script_error, ScriptError, validate_environment_vars, logger

def print_progress(message: str, emoji: str) -> None:
    """Print progress messages with emoji."""
    logger.info(f"{emoji} {message}")

def validate_json_value(value: str, var_name: str) -> Any:
    """Validate and parse JSON string values."""
    if not value:
        return None
        
    try:
        if value.startswith('{') or value.startswith('['):
            return json.loads(value)
        return value
    except json.JSONDecodeError as e:
        raise ScriptError(
            f"Invalid JSON format for variable {var_name}: {str(e)}",
            exit_code=3
        )

def create_tfvars(module_vars: Dict[str, Any], output_path: Path) -> None:
    """Create terraform.tfvars.json file from module variables."""
    tfvars = {}
    missing_vars = []

    # Process each variable from module variables
    for var_name, var_config in module_vars.items():
        env_var_value = os.environ.get(var_name)
        
        if env_var_value is not None:
            # Convert environment variable value to appropriate type
            try:
                if var_config.get('type') == 'bool':
                    tfvars[var_name] = env_var_value.lower() in ['true', '1', 'yes']
                elif var_config.get('type') == 'number':
                    tfvars[var_name] = float(env_var_value)
                else:
                    # Handle potential JSON strings (lists, maps)
                    tfvars[var_name] = validate_json_value(env_var_value, var_name)
            except ValueError as e:
                raise ScriptError(
                    f"Invalid value for variable '{var_name}': {str(e)}",
                    exit_code=3
                )
        elif var_config.get('required', False):
            missing_vars.append(var_name)
        elif 'default' in var_config:
            tfvars[var_name] = var_config['default']

    if missing_vars:
        raise ScriptError(
            f"Missing required variables: {', '.join(missing_vars)}",
            exit_code=2
        )

    # Create parent directory if it doesn't exist
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write tfvars to file
    try:
        with output_path.open('w') as f:
            json.dump(tfvars, f, indent=2)
    except IOError as e:
        raise ScriptError(
            f"Failed to write terraform.tfvars.json: {str(e)}",
            exit_code=4
        )

@handle_script_error
def main():
    # Validate required environment variables
    validate_environment_vars("MODULE_PATH", "MODULE_VARS_FILE")
    
    module_path = Path(os.environ["MODULE_PATH"])
    module_vars_file = Path(os.environ["MODULE_VARS_FILE"])
    
    print_progress("Starting tfvars preparation...", "🚀")
    
    try:
        # Validate module variables file exists
        if not module_vars_file.exists():
            raise ScriptError(
                f"Module variables file not found: {module_vars_file}",
                exit_code=2
            )

        # Read module variables
        try:
            with module_vars_file.open() as f:
                module_vars = json.load(f)
        except json.JSONDecodeError as e:
            raise ScriptError(
                f"Invalid JSON in module variables file: {str(e)}",
                exit_code=3
            )
        except IOError as e:
            raise ScriptError(
                f"Failed to read module variables file: {str(e)}",
                exit_code=4
            )

        # Validate module path exists
        if not module_path.exists():
            raise ScriptError(
                f"Module path does not exist: {module_path}",
                exit_code=2
            )

        # Create tfvars file
        tfvars_path = module_path / 'terraform.tfvars.json'
        print_progress(f"Creating terraform.tfvars.json at {tfvars_path}", "📝")
        create_tfvars(module_vars, tfvars_path)

    except ScriptError:
        raise
    except Exception as e:
        raise ScriptError(f"Unexpected error: {str(e)}", exit_code=1)

    print_progress("Successfully prepared terraform.tfvars.json", "✅")

if __name__ == "__main__":
    main() 