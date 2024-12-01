import os
import json
import tempfile
import subprocess
from typing import Dict, Any, List, Optional, Tuple
import logging
import re

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
        self.readme_url = None  # To store README.md URL if it exists

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
        variables = {}
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
                # First check module directory
                variables_files = []
                module_vars_file = os.path.join(module_dir, 'variables.tf')
                if os.path.exists(module_vars_file):
                    logger.info(f"Found variables.tf in module directory: {module_vars_file}")
                    variables_files.append(module_vars_file)

                # Then check root directory if we're in a subdirectory
                if self.path:
                    root_vars_file = os.path.join(temp_dir, 'variables.tf')
                    if os.path.exists(root_vars_file):
                        logger.info(f"Found variables.tf in root directory: {root_vars_file}")
                        variables_files.append(root_vars_file)

                # If no variables.tf found, look for other .tf files
                if not variables_files:
                    for root, _, files in os.walk(module_dir):
                        for file in files:
                            if file.endswith('.tf'):
                                file_path = os.path.join(root, file)
                                variables_files.append(file_path)

                if not variables_files:
                    raise ValueError("No Terraform files found in module")

                # Parse variables from all found files
                for var_file in variables_files:
                    logger.info(f"Parsing variables from: {var_file}")
                    try:
                        vars_in_file = self._parse_variables_file(var_file)
                        variables.update(vars_in_file)
                    except Exception as e:
                        self.warnings.append(f"Failed to parse {var_file}: {str(e)}")

                if not variables:
                    raise ValueError("No variables found in module")

                # Get README.md URL if it exists
                readme_path = os.path.join(module_dir, 'README.md')
                if os.path.exists(readme_path):
                    # Construct the GitHub URL to the README.md file
                    repo_name = github_url.rstrip('/').split('/')[-1]
                    if self.ref:
                        self.readme_url = f"{github_url}/blob/{self.ref}/README.md"
                    else:
                        self.readme_url = f"{github_url}/blob/master/README.md"
                    logger.info(f"Found README.md at: {self.readme_url}")

                logger.info(f"Successfully parsed {len(variables)} variables")
                
                # Ensure variable descriptions are captured
                for var_name, var_config in variables.items():
                    if 'description' not in var_config or not var_config['description']:
                        var_config['description'] = 'No description provided'

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
            logger.debug(f"Raw variable blocks: {json.dumps(var_blocks, indent=2)}")

            # Handle both list and dict formats from hcl2json
            if isinstance(var_blocks, list):
                # Handle list format where each item is a dict with a single key
                for var_block in var_blocks:
                    if not isinstance(var_block, dict):
                        error_msg = f"Invalid variable block format: {var_block}"
                        logger.error(error_msg)
                        raise ValueError(error_msg)

                    for var_name, var_config in var_block.items():
                        processed_var = self._process_variable(var_name, var_config)
                        variables[var_name] = processed_var
            else:
                # Handle dict format
                if not isinstance(var_blocks, dict):
                    error_msg = f"Invalid variables format: expected dict, got {type(var_blocks)}"
                    logger.error(error_msg)
                    raise ValueError(error_msg)

                for var_name, var_config in var_blocks.items():
                    processed_var = self._process_variable(var_name, var_config)
                    variables[var_name] = processed_var

            logger.debug(f"Found variables: {json.dumps(variables, indent=2)}")

        return variables

    def _process_variable(self, var_name: str, var_config: Dict[str, Any]) -> Dict[str, Any]:
        """Process individual variable configuration."""
        if not isinstance(var_config, dict):
            error_msg = f"Invalid variable config format for {var_name}: {var_config}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        # Extract type, default, and description
        var_type = var_config.get('type', 'string')
        default = var_config.get('default')
        description = var_config.get('description', '')

        # Clean up type string (remove interpolation syntax if any)
        if isinstance(var_type, str):
            var_type = re.sub(r'^\${(.*)}$', r'\1', var_type)
            var_type = var_type.strip()

        # Handle complex types by defaulting to 'string'
        if var_type not in ['string', 'str', 'number', 'bool']:
            logger.warning(f"Unsupported variable type '{var_type}' for variable '{var_name}'. Defaulting type to 'string'.")
            var_type = 'string'

        # Determine if variable is required
        required = 'default' not in var_config

        processed_var = {
            'type': var_type,
            'description': description,
            'default': default,
            'required': required
        }
        logger.debug(f"Processed variable {var_name}: {processed_var}")
        return processed_var