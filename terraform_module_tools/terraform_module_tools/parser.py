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
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache

logger = logging.getLogger(__name__)

# Cache the hcl2json binary download
@lru_cache(maxsize=1)
def ensure_hcl2json():
    HCL2JSON_PATH = '/usr/local/bin/hcl2json'
    if not os.path.exists(HCL2JSON_PATH):
        response = requests.get('https://github.com/tmccombs/hcl2json/releases/download/v0.6.4/hcl2json_linux_amd64')
        with open(HCL2JSON_PATH, 'wb') as f:
            f.write(response.content)
        os.chmod(HCL2JSON_PATH, 0o755)
    return HCL2JSON_PATH

class TerraformModuleParser:
    def __init__(
        self,
        source_url: str,
        ref: Optional[str] = None,
        path: Optional[str] = None,
        max_workers: int = 4  # Number of parallel workers
    ):
        self.source_url = source_url
        self.ref = ref
        self.path = path
        self.warnings = []
        self.errors = []
        self.readme_url = None
        self.module_dir = None
        self.max_workers = max_workers
        self._clone_repository()
        ensure_hcl2json()

    @lru_cache(maxsize=128)
    def _get_github_url(self) -> str:
        """Convert module source to GitHub URL with caching."""
        if self.source_url.startswith(('http://', 'https://', 'git@')):
            return self.source_url

        if self.source_url.startswith('terraform-aws-modules/'):
            parts = self.source_url.split('/')
            if len(parts) != 3:
                raise ValueError(f"Invalid module format: {self.source_url}")
            _, provider, name = parts
            return f"https://github.com/terraform-aws-modules/terraform-{provider}-{name}"

        raise ValueError(f"Unsupported source format: {self.source_url}")

    def _clone_repository(self) -> None:
        """Clone the repository with optimized git operations."""
        github_url = self._get_github_url()
        temp_dir = tempfile.mkdtemp()

        try:
            logger.info(f"Cloning repository: {github_url}")
            # Use shallow clone to speed up the process
            clone_cmd = [
                'git', 'clone', '--depth', '1', 
                '--single-branch'
            ]
            
            if self.ref:
                clone_cmd.extend(['--branch', self.ref])
            
            if "GH_TOKEN" in os.environ:
                auth_url = github_url.replace(
                    "https://github.com",
                    f"https://{os.environ['GH_TOKEN']}@github.com"
                )
                clone_cmd.append(auth_url)
            else:
                clone_cmd.append(github_url)
            
            clone_cmd.append(str(temp_dir))
            
            subprocess.run(clone_cmd, check=True, capture_output=True)
            
            # Set the module directory
            self.module_dir = os.path.join(temp_dir, self.path or '')
            if self.path and not os.path.exists(self.module_dir):
                raise ValueError(f"Specified path '{self.path}' does not exist")

            # Set README URL if exists
            readme_path = os.path.join(self.module_dir, 'README.md')
            if os.path.exists(readme_path):
                self.readme_url = os.path.join(
                    github_url.replace('.git', ''),
                    'blob',
                    self.ref or 'master',
                    self.path or '',
                    'README.md'
                )

        except subprocess.CalledProcessError as e:
            error_msg = f"Failed to clone repository {github_url}: {e.stderr}"
            logger.error(error_msg)
            raise ValueError(error_msg)

    def _parse_variables_file(self, file_path: str) -> Dict[str, Any]:
        """Parse variables from a Terraform file with error handling."""
        try:
            result = subprocess.run(
                ['/usr/local/bin/hcl2json', file_path],
                capture_output=True,
                text=True,
                check=True,
                timeout=10
            )
            
            tf_json = json.loads(result.stdout)
            variables = {}

            if 'variable' in tf_json:
                var_blocks = tf_json['variable']
                
                # Handle both list and dict formats
                if isinstance(var_blocks, dict):
                    # Direct dictionary format
                    for var_name, var_config in var_blocks.items():
                        if isinstance(var_config, list):
                            # Take first element if it's a list
                            var_config = var_config[0] if var_config else {}
                        processed_var = self._process_variable(var_name, var_config)
                        if processed_var:
                            variables[var_name] = processed_var
                elif isinstance(var_blocks, list):
                    # List of single-key dictionaries format
                    for var_block in var_blocks:
                        if isinstance(var_block, dict):
                            for var_name, var_config in var_block.items():
                                if isinstance(var_config, list):
                                    var_config = var_config[0] if var_config else {}
                                processed_var = self._process_variable(var_name, var_config)
                                if processed_var:
                                    variables[var_name] = processed_var

            return variables

        except subprocess.TimeoutExpired:
            logger.error(f"Timeout while parsing {file_path}")
            return {}
        except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
            logger.error(f"Failed to parse {file_path}: {str(e)}")
            return {}

    def get_variables(self) -> Tuple[Dict[str, Any], List[str], List[str]]:
        """Parse variables from Terraform module with parallel processing."""
        variables = {}
        
        try:
            # Find all .tf files
            tf_files = glob.glob(os.path.join(self.module_dir, '**', '*.tf'), recursive=True)
            
            if not tf_files:
                self.errors.append("No .tf files found in module")
                return {}, self.warnings, self.errors

            # Process files in parallel
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_file = {
                    executor.submit(self._parse_variables_file, tf_file): tf_file
                    for tf_file in tf_files
                }
                
                for future in as_completed(future_to_file):
                    tf_file = future_to_file[future]
                    try:
                        vars_in_file = future.result()
                        variables.update(vars_in_file)
                    except Exception as e:
                        logger.error(f"Failed to process {tf_file}: {str(e)}")

        except Exception as e:
            logger.error(f"Failed to get variables: {str(e)}", exc_info=True)
            self.errors.append(f"Failed to get variables: {str(e)}")
        finally:
            # Clean up the cloned repository
            if self.module_dir and os.path.exists(os.path.dirname(self.module_dir)):
                shutil.rmtree(os.path.dirname(self.module_dir))
                logger.info(f"Cleaned up temporary directory: {self.module_dir}")

        if not variables:
            self.errors.append("No variables found in module")

        return variables, self.warnings, self.errors

    def _process_variable(self, var_name: str, var_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process individual variable configuration."""
        try:
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
                logger.warning(f"Complex type '{var_type}' for variable '{var_name}' will be handled as 'string'")
                var_type = 'str'

            # Determine if variable is required
            required = 'default' not in var_config

            processed_var = {
                'type': var_type,
                'description': description,
                'default': default if default is not None else None,
                'required': required
            }
            return processed_var

        except Exception as e:
            logger.warning(f"Failed to process variable {var_name}: {str(e)}")
            return None