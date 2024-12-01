#!/usr/bin/env python3
import os
import sys
import json
import subprocess
import tempfile
import re
from typing import Dict, Any, List

def print_progress(message: str, emoji: str) -> None:
    """Print progress messages with emoji."""
    print(f"\n{emoji} {message}", flush=True)
    sys.stdout.flush()

def parse_variable_block(content: str) -> Dict[str, Any]:
    """Parse a Terraform variable block and extract information."""
    description = re.search(r'description\s*=\s*"([^"]+)"', content)
    type_match = re.search(r'type\s*=\s*(\w+)', content)
    default = re.search(r'default\s*=\s*([^\n]+)', content)
    
    return {
        "description": description.group(1) if description else None,
        "type": type_match.group(1) if type_match else "string",
        "default": default.group(1).strip() if default else None,
        "required": default is None
    }

def get_module_variables(module_url: str) -> Dict[str, Any]:
    """Get variables from a Terraform module."""
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            # Clone repository
            print_progress("Cloning repository...", "📦")
            clone_cmd = ["git", "clone"]
            if "GH_TOKEN" in os.environ:
                auth_url = module_url.replace(
                    "https://github.com",
                    f"https://{os.environ['GH_TOKEN']}@github.com"
                )
                clone_cmd.append(auth_url)
            else:
                clone_cmd.append(module_url)
            
            clone_cmd.append(temp_dir)
            subprocess.run(clone_cmd, check=True, capture_output=True)

            # Find all .tf files
            variables = {}
            for root, _, files in os.walk(temp_dir):
                for file in files:
                    if file.endswith('.tf'):
                        file_path = os.path.join(root, file)
                        with open(file_path, 'r') as f:
                            content = f.read()
                            
                            # Find all variable blocks
                            var_blocks = re.finditer(
                                r'variable\s+"([^"]+)"\s*{([^}]+)}',
                                content,
                                re.MULTILINE | re.DOTALL
                            )
                            
                            for var_block in var_blocks:
                                var_name = var_block.group(1)
                                var_content = var_block.group(2)
                                variables[var_name] = parse_variable_block(var_content)

            return {
                "variables": variables,
                "total_count": len(variables),
                "required_count": sum(1 for v in variables.values() if v["required"]),
                "optional_count": sum(1 for v in variables.values() if not v["required"])
            }

        except Exception as e:
            print(f"Error: {str(e)}", file=sys.stderr)
            sys.exit(1)

def main():
    if len(sys.argv) != 2:
        print("Usage: get_module_vars.py <module_url>", file=sys.stderr)
        sys.exit(1)

    module_url = sys.argv[1]
    result = get_module_variables(module_url)
    
    # Print results in a nice format
    print("\n📋 Module Variables Summary:")
    print(f"Total Variables: {result['total_count']}")
    print(f"Required Variables: {result['required_count']}")
    print(f"Optional Variables: {result['optional_count']}")
    print("\nDetailed Variables:")
    
    for var_name, var_info in result['variables'].items():
        print(f"\n🔹 {var_name}:")
        print(f"  Description: {var_info['description'] or 'No description'}")
        print(f"  Type: {var_info['type']}")
        print(f"  Required: {'Yes' if var_info['required'] else 'No'}")
        if var_info['default'] is not None:
            print(f"  Default: {var_info['default']}")
    
    # Output JSON for tool consumption
    print("\nJSON_OUTPUT_START")
    print(json.dumps(result))
    print("JSON_OUTPUT_END")

if __name__ == "__main__":
    main() 