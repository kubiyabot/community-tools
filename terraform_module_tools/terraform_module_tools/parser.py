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
        result = subprocess.run(
            ['hcl2json', file_path],
            capture_output=True,
            text=True,
            check=True
        )

        # Parse JSON output
        tf_json = json.loads(result.stdout)
        variables = {}

        if 'variable' in tf_json:
            for var_name, var_config in tf_json['variable'].items():
                variables[var_name] = {
                    'type': var_config.get('type', 'string'),
                    'description': var_config.get('description', ''),
                    'default': var_config.get('default'),
                    'required': 'default' not in var_config
                }
                logger.debug(f"Found variable: {var_name} ({variables[var_name]})")

        return variables