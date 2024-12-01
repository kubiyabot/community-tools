import os
import json
import tempfile
import subprocess
from typing import Dict, Any, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class TerraformModuleParser:
    def __init__(
        self,
        source_url: str,
        ref: Optional[str] = None,
        path: Optional[str] = None
    ):
        """Initialize parser with GitHub source.
        
        Args:
            source_url: Module source (e.g., 'terraform-aws-modules/vpc/aws')
            ref: Git reference (e.g., 'v5.1.2')
            path: Path to module within repository
        """
        self.source_url = source_url
        self.ref = ref
        self.path = path
        self.warnings = []
        self.errors = []

    def _get_github_url(self) -> str:
        """Convert module source to GitHub URL."""
        if self.source_url.startswith(('http://', 'https://', 'git@')):
            return self.source_url

        # Handle terraform-aws-modules format
        if self.source_url.startswith('terraform-aws-modules/'):
            parts = self.source_url.split('/')
            if len(parts) != 3:
                raise ValueError(f"Invalid module format: {self.source_url}")
            _, provider, name = parts
            return f"https://github.com/terraform-aws-modules/terraform-{provider}-{name}"

        raise ValueError(f"Unsupported source format: {self.source_url}")

    def get_variables(self) -> Tuple[Dict[str, Any], List[str], List[str]]:
        """Get variables from the Terraform module."""
        try:
            # Get GitHub URL
            github_url = self._get_github_url()
            logger.info(f"Using GitHub URL: {github_url}")

            # Create temporary directory
            with tempfile.TemporaryDirectory() as temp_dir:
                # Clone repository
                logger.info(f"Cloning repository: {github_url}")
                subprocess.run(
                    ['git', 'clone', github_url, temp_dir],
                    check=True,
                    capture_output=True,
                    text=True
                )

                # Checkout specific ref if provided
                if self.ref:
                    logger.info(f"Checking out ref: {self.ref}")
                    subprocess.run(
                        ['git', 'checkout', self.ref],
                        cwd=temp_dir,
                        check=True,
                        capture_output=True,
                        text=True
                    )

                # Get module directory
                module_dir = os.path.join(temp_dir, self.path) if self.path else temp_dir
                if not os.path.exists(module_dir):
                    raise ValueError(f"Module path not found: {self.path}")

                # Look for variables.tf in both root and module directory
                variables = {}
                
                # First check module directory
                module_vars_file = os.path.join(module_dir, 'variables.tf')
                if os.path.exists(module_vars_file):
                    logger.info(f"Found variables.tf in module directory: {module_vars_file}")
                    module_vars = self._parse_variables_file(module_vars_file)
                    variables.update(module_vars)
                
                # Then check root directory if we're in a subdirectory
                if self.path:
                    root_vars_file = os.path.join(temp_dir, 'variables.tf')
                    if os.path.exists(root_vars_file):
                        logger.info(f"Found variables.tf in root directory: {root_vars_file}")
                        root_vars = self._parse_variables_file(root_vars_file)
                        variables.update(root_vars)

                if not variables:
                    # Look for any .tf files that might contain variables
                    for root, _, files in os.walk(module_dir):
                        for file in files:
                            if file.endswith('.tf'):
                                file_path = os.path.join(root, file)
                                logger.info(f"Checking {file_path} for variables")
                                try:
                                    vars_in_file = self._parse_variables_file(file_path)
                                    variables.update(vars_in_file)
                                except Exception as e:
                                    self.warnings.append(f"Failed to parse {file_path}: {str(e)}")

                if not variables:
                    raise ValueError("No variables found in module")

                logger.info(f"Successfully parsed {len(variables)} variables")
                return variables, self.warnings, self.errors

        except subprocess.CalledProcessError as e:
            error_msg = f"Git operation failed: {e.stderr}"
            self.errors.append(error_msg)
            logger.error(error_msg)
            return {}, self.warnings, self.errors
        except Exception as e:
            error_msg = f"Failed to get variables: {str(e)}"
            self.errors.append(error_msg)
            logger.error(error_msg)
            return {}, self.warnings, self.errors

    def _parse_variables_file(self, file_path: str) -> Dict[str, Any]:
        """Parse variables from a Terraform file."""
        logger.info(f"Parsing variables from: {file_path}")
        try:
            result = subprocess.run(
                ['hcl2json', file_path],
                capture_output=True,
                text=True,
                check=True
            )
        except subprocess.CalledProcessError as e:
            error_msg = f"hcl2json failed to parse {file_path}: {e.stderr}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        # Parse JSON output
        try:
            tf_json = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse hcl2json output: {str(e)}\nOutput was: {result.stdout}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        variables = {}

        # Handle variable blocks
        if 'variable' in tf_json:
            var_blocks = tf_json['variable']
            logger.debug(f"Raw variable blocks from {file_path}: {json.dumps(var_blocks, indent=2)}")
            
            # Handle both list and dict formats from hcl2json
            if isinstance(var_blocks, list):
                # Handle list format where each item is a dict with a single key
                for var_block in var_blocks:
                    if not isinstance(var_block, dict):
                        logger.warning(f"Invalid variable block format: {var_block}")
                        continue
                    
                    for var_name, var_config in var_block.items():
                        if not isinstance(var_config, dict):
                            logger.warning(f"Invalid variable config format for {var_name}: {var_config}")
                            continue
                        
                        # Clean up type string (handle ${type} format)
                        var_type = var_config.get('type', 'string')
                        if isinstance(var_type, str):
                            var_type = var_type.replace('${', '').replace('}', '')
                        elif isinstance(var_type, list) and len(var_type) > 0:
                            # Sometimes type comes as a list with one item
                            if isinstance(var_type[0], dict):
                                type_value = var_type[0].get('type', 'string')
                                var_type = type_value.replace('${', '').replace('}', '')
                            else:
                                var_type = str(var_type[0]).replace('${', '').replace('}', '')
                        
                        # Generate example value based on type
                        example = self._generate_example(var_name, var_type, var_config)
                        
                        # Handle default value
                        default = var_config.get('default')
                        if isinstance(default, (dict, list)):
                            default = json.dumps(default)
                        
                        variables[var_name] = {
                            'type': var_type,
                            'description': var_config.get('description', ''),
                            'default': default,
                            'required': 'default' not in var_config,
                            'example': example
                        }
                        logger.debug(f"Added variable {var_name}: {variables[var_name]}")
            else:
                # Handle dict format
                if not isinstance(var_blocks, dict):
                    logger.warning(f"Invalid variables format: {type(var_blocks)}")
                    return variables
                
                for var_name, var_config in var_blocks.items():
                    if not isinstance(var_config, dict):
                        logger.warning(f"Invalid variable config format for {var_name}: {var_config}")
                        continue
                    
                    # Clean up type string (handle ${type} format)
                    var_type = var_config.get('type', 'string')
                    if isinstance(var_type, str):
                        var_type = var_type.replace('${', '').replace('}', '')
                    elif isinstance(var_type, list) and len(var_type) > 0:
                        # Sometimes type comes as a list with one item
                        if isinstance(var_type[0], dict):
                            type_value = var_type[0].get('type', 'string')
                            var_type = type_value.replace('${', '').replace('}', '')
                        else:
                            var_type = str(var_type[0]).replace('${', '').replace('}', '')
                    
                    # Generate example value based on type
                    example = self._generate_example(var_name, var_type, var_config)
                    
                    # Handle default value
                    default = var_config.get('default')
                    if isinstance(default, (dict, list)):
                        default = json.dumps(default)
                    
                    variables[var_name] = {
                        'type': var_type,
                        'description': var_config.get('description', ''),
                        'default': default,
                        'required': 'default' not in var_config,
                        'example': example
                    }
                    logger.debug(f"Added variable {var_name}: {variables[var_name]}")

            logger.debug(f"Found {len(variables)} variables in {file_path}")

        return variables

    def _generate_example(self, var_name: str, var_type: str, var_config: Dict[str, Any]) -> str:
        """Generate example value based on variable name and type."""
        # Check for default value first
        if 'default' in var_config:
            if isinstance(var_config['default'], (dict, list)):
                return json.dumps(var_config['default'], indent=2)
            return str(var_config['default'])

        # Handle different types
        base_type = var_type.split('(')[0].lower()
        
        # Common patterns in variable names
        if 'name' in var_name:
            return '"example-name"'
        elif 'cidr' in var_name:
            return '"10.0.0.0/16"'
        elif 'region' in var_name:
            return '"us-west-2"'
        elif 'enabled' in var_name or base_type == 'bool':
            return 'true'
        elif base_type == 'number':
            return '42'
        
        # Complex types
        elif base_type == 'list':
            if 'string' in var_type:
                return '["value1", "value2"]'
            elif 'number' in var_type:
                return '[1, 2, 3]'
            elif 'bool' in var_type:
                return '[true, false]'
            return '["example1", "example2"]'
        
        elif base_type == 'map':
            if 'string' in var_type:
                return '{"key1": "value1", "key2": "value2"}'
            elif 'number' in var_type:
                return '{"key1": 1, "key2": 2}'
            elif 'bool' in var_type:
                return '{"key1": true, "key2": false}'
            return '{"example_key": "example_value"}'
        
        elif base_type == 'object':
            return '''{
  "field1": "value1",
  "field2": "value2",
  "nested": {
    "key": "value"
  }
}'''
        
        # Default to string
        return '"example-value"'