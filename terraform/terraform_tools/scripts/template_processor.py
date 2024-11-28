import json
import re
from typing import Dict, Any, Optional, Tuple, List
from jinja2 import Environment, BaseLoader
import logging

logger = logging.getLogger(__name__)

class TerraformTemplateProcessor:
    def __init__(self):
        self.jinja_env = Environment(
            loader=BaseLoader(),
            variable_start_string='${',
            variable_end_string='}',
            keep_trailing_newline=True
        )

    def _parse_variable_definition(self, definition: str) -> Dict[str, Any]:
        """Parse a variable definition string into its components."""
        pattern = r"(\w+)(?:\(((?:required|default=.+))\))?"
        match = re.match(pattern, definition)
        if not match:
            raise ValueError(f"Invalid variable definition: {definition}")

        var_type, var_config = match.groups()
        result = {"type": var_type}

        if var_config:
            if var_config == "required":
                result["required"] = True
            elif var_config.startswith("default="):
                default_value = var_config[8:]  # Remove "default="
                # Handle different types
                if var_type == "bool":
                    result["default"] = default_value.lower() == "true"
                elif var_type == "number":
                    result["default"] = float(default_value)
                elif var_type == "list":
                    result["default"] = [v.strip() for v in default_value.strip("[]").split(",")]
                else:
                    result["default"] = default_value
                result["required"] = False

        return result

    def _process_generate_block(self, generate_block: Dict[str, Any], variables: Dict[str, Any]) -> Dict[str, Any]:
        """Process a generate block with variables."""
        def replace_vars(obj: Any) -> Any:
            if isinstance(obj, str):
                # Handle for_each special case
                if obj.startswith("${") and obj.endswith("}"):
                    var_name = obj[2:-1]
                    return variables.get(var_name, obj)
                return obj
            elif isinstance(obj, dict):
                if "for_each" in obj:
                    # Handle for_each construct
                    items = variables.get(obj["for_each"][2:-1], {})
                    result = {}
                    for key, value in items.items():
                        new_obj = {k: v for k, v in obj.items() if k != "for_each"}
                        ctx = {"each": {"key": key, "value": value}, **variables}
                        result[key] = replace_vars_with_context(new_obj, ctx)
                    return result
                return {k: replace_vars(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [replace_vars(item) for item in obj]
            return obj

        def replace_vars_with_context(obj: Any, context: Dict[str, Any]) -> Any:
            if isinstance(obj, str):
                if obj.startswith("${") and obj.endswith("}"):
                    template = self.jinja_env.from_string(obj[2:-1])
                    return template.render(**context)
                return obj
            elif isinstance(obj, dict):
                return {k: replace_vars_with_context(v, context) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [replace_vars_with_context(item, context) for item in obj]
            return obj

        return replace_vars(generate_block)

    def process_module(self, module_config: Dict[str, Any], input_variables: Dict[str, Any]) -> Dict[str, Any]:
        """Process a module configuration with variables."""
        try:
            # Process variables
            processed_vars = {}
            for var_name, var_def in module_config.get("variables", {}).items():
                if isinstance(var_def, str):
                    # Simple variable definition
                    var_config = self._parse_variable_definition(var_def)
                    if var_name in input_variables:
                        processed_vars[var_name] = input_variables[var_name]
                    elif "default" in var_config:
                        processed_vars[var_name] = var_config["default"]
                    elif var_config.get("required", False):
                        raise ValueError(f"Required variable {var_name} not provided")
                elif isinstance(var_def, dict):
                    # Complex variable definition with schema
                    if "generate" in var_def:
                        # Process generate block for this variable
                        processed_vars[var_name] = self._process_generate_block(
                            var_def["generate"],
                            input_variables.get(var_name, {})
                        )
                    else:
                        processed_vars[var_name] = input_variables.get(var_name, {})

            # Process template if present
            if "template" in module_config:
                if "generate" in module_config["template"]:
                    result = self._process_generate_block(
                        module_config["template"]["generate"],
                        processed_vars
                    )
                    return {
                        "content": json.dumps(result, indent=2),
                        "variables": processed_vars
                    }

            return {
                "variables": processed_vars
            }

        except Exception as e:
            logger.error(f"Error processing module template: {e}")
            raise

__all__ = ['TerraformTemplateProcessor'] 