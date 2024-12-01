import os
import json
import tempfile
import subprocess
from typing import Dict, Any, List, Optional, Tuple
import logging
import re
import glob
import shutil
import requests
logger = logging.getLogger(__name__)

HCL2JSON_PATH = '/usr/local/bin/hcl2json'

if not os.path.exists(HCL2JSON_PATH):
    # Download using requests
    response = requests.get('https://github.com/tmccombs/hcl2json/releases/download/v0.6.4/hcl2json_linux_amd64')
    with open(HCL2JSON_PATH, 'wb') as f:
        f.write(response.content)
    os.chmod(HCL2JSON_PATH, 0o755)

# if the binary is not found, raise an error
if not os.path.exists(HCL2JSON_PATH):
    raise ValueError("hcl2json binary not found. The discovery process has tried to install it directly but failed. Please install it manually on the base image of the tool manager SDK container on namespace kubiya on your cluster.")

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
        self.module_dir = None  # Will be set after cloning
        self._clone_repository()

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

    def _clone_repository(self) -> None:
        """Clone the repository and set the module directory."""
        github_url = self._get_github_url()
        temp_dir = tempfile.mkdtemp()

        try:
            logger.info(f"Cloning repository: {github_url}")
            subprocess.run(['git', 'clone', github_url, temp_dir], check=True)

            if self.ref:
                logger.info(f"Checking out ref: {self.ref}")
                subprocess.run(['git', '-C', temp_dir, 'checkout', self.ref], check=True)

            # Set the module directory based on the provided path
            if self.path:
                self.module_dir = os.path.join(temp_dir, self.path)
                if not os.path.exists(self.module_dir):
                    error_msg = f"Specified path '{self.path}' does not exist in the repository"
                    logger.error(error_msg)
                    raise ValueError(error_msg)
            else:
                self.module_dir = temp_dir

            logger.info(f"Repository cloned to: {self.module_dir}")

            # Optionally, set the README URL
            readme_path = os.path.join(self.module_dir, 'README.md')
            if os.path.exists(readme_path):
                self.readme_url = os.path.join(github_url.replace('.git', ''), 'blob', self.ref or 'master', self.path or '', 'README.md')
                logger.info(f"README.md found at: {self.readme_url}")

        except subprocess.CalledProcessError as e:
            error_msg = f"Failed to clone repository {github_url}: {e.stderr}"
            logger.error(error_msg)
            raise ValueError(error_msg)

    def get_variables(self) -> Tuple[Dict[str, Any], List[str], List[str]]:
        """Parse variables from Terraform module."""
        variables = {}
        warnings = []
        errors = []

        try:
            # Search for all .tf files in the module directory recursively
            tf_files = glob.glob(os.path.join(self.module_dir, '**', '*.tf'), recursive=True)
            if not tf_files:
                errors.append("No .tf files found in module")
            else:
                for tf_file in tf_files:
                    logger.info(f"Parsing variables from: {tf_file}")
                    vars_in_file = self._parse_variables_file(tf_file)
                    variables.update(vars_in_file)
            if not variables:
                errors.append("No variables found in module")
        except Exception as e:
            logger.error(f"Failed to get variables: {str(e)}", exc_info=True)
            errors.append(f"Failed to get variables: {str(e)}")
        finally:
            # Clean up the cloned repository to free up space
            if self.module_dir and os.path.exists(self.module_dir):
                shutil.rmtree(self.module_dir)
                logger.info(f"Cleaned up temporary directory: {self.module_dir}")
        return variables, warnings, errors

    def _parse_variables_file(self, file_path: str) -> Dict[str, Any]:
        """Parse variables from a Terraform file."""
        logger.info(f"Parsing variables from: {file_path}")
        try:
            result = subprocess.run(
                ['/usr/local/bin/hcl2json', file_path],
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

                    for var_name, var_configs in var_block.items():
                        # var_configs might be a list
                        if isinstance(var_configs, list):
                            for var_config in var_configs:
                                processed_var = self._process_variable(var_name, var_config)
                                variables[var_name] = processed_var
                        elif isinstance(var_configs, dict):
                            processed_var = self._process_variable(var_name, var_configs)
                            variables[var_name] = processed_var
                        else:
                            error_msg = f"Invalid variable config format for {var_name}: {var_configs}"
                            logger.error(error_msg)
                            raise ValueError(error_msg)
            elif isinstance(var_blocks, dict):
                # Handle dict format
                for var_name, var_configs in var_blocks.items():
                    if isinstance(var_configs, list):
                        for var_config in var_configs:
                            processed_var = self._process_variable(var_name, var_config)
                            variables[var_name] = processed_var
                    elif isinstance(var_configs, dict):
                        processed_var = self._process_variable(var_name, var_configs)
                        variables[var_name] = processed_var
                    else:
                        error_msg = f"Invalid variable config format for {var_name}: {var_configs}"
                        logger.error(error_msg)
                        raise ValueError(error_msg)
            else:
                error_msg = f"Unexpected format for variable blocks: {type(var_blocks)}"
                logger.error(error_msg)
                raise ValueError(error_msg)

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
            var_type = 'str'

        # Determine if variable is required
        required = 'default' not in var_config

        processed_var = {
            'type': var_type,
            'description': description,
            'default': default if default is not None else None,
            'required': required
        }
        logger.debug(f"Processed variable {var_name}: {processed_var}")
        return processed_var