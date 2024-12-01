#!/usr/bin/env python3
import os
import sys
import json

def main():
    if len(sys.argv) != 2:
        print("Usage: prepare_tfvars.py <module_variables_file>", file=sys.stderr)
        sys.exit(1)
    
    module_variables_file = sys.argv[1]

    # Read module variables signature
    with open(module_variables_file, 'r') as f:
        variables = json.load(f)

    tfvars = {}
    missing_vars = []

    for var_name, var_config in variables.items():
        env_var_value = os.environ.get(var_name)
        if env_var_value is not None:
            # Convert environment variable value to appropriate type
            var_type = var_config.get('type')
            if var_type == 'int':
                try:
                    env_var_value = int(env_var_value)
                except ValueError:
                    print(f"Invalid value for variable '{var_name}': expected integer.", file=sys.stderr)
                    sys.exit(1)
            elif var_type == 'bool':
                env_var_value = env_var_value.lower() in ['true', '1', 'yes']
            tfvars[var_name] = env_var_value
        elif var_config.get('required', False):
            missing_vars.append(var_name)
        elif 'default' in var_config and var_config['default'] is not None:
            tfvars[var_name] = var_config['default']

    if missing_vars:
        print(f"Missing required variables: {', '.join(missing_vars)}", file=sys.stderr)
        sys.exit(1)

    # Write tfvars to file
    with open('terraform.tfvars.json', 'w') as f:
        json.dump(tfvars, f, indent=2)

if __name__ == "__main__":
    main() 