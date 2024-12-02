#!/usr/bin/env python3
import os
import json
from pathlib import Path
from typing import Dict, Any
from terraform_tools.error_handler import handle_script_error, ScriptError, validate_environment_vars, logger

def get_module_vars() -> Dict[str, Any]:
    """Get module variables from the module_variables.json file."""
    validate_environment_vars("MODULE_VARS_FILE")
    
    module_vars_file = Path(os.environ["MODULE_VARS_FILE"])
    
    try:
        if not module_vars_file.exists():
            raise ScriptError(
                f"Module variables file not found: {module_vars_file}",
                exit_code=2
            )

        with module_vars_file.open() as f:
            return json.load(f)
            
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

@handle_script_error
def main():
    """Main function to print module variables."""
    vars = get_module_vars()
    print(json.dumps(vars, indent=2))

if __name__ == "__main__":
    main() 