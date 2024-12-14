import os
import json
import tempfile
import subprocess
from typing import Dict, Any, List, Optional, Tuple, Set
import logging
import re
import glob
import shutil
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
from kubiya_sdk.tools.models import FileSpec

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
    PROVIDER_REQUIREMENTS = {
        'aws': {
            'env': ['AWS_PROFILE'],
            'files': [
                FileSpec(source="$HOME/.aws/credentials", destination="/root/.aws/credentials"),
                FileSpec(source="$HOME/.aws/config", destination="/root/.aws/config"),
            ]
        },
        'github': {
            'env': [],  # No env vars needed since GH_TOKEN is already in secrets
            'files': []
        }
    }

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
        self.providers: Set[str] = set()
        self._clone_repository()
        ensure_hcl2json()

    @lru_cache(maxsize=128)
    def _get_github_url(self) -> str:
        """Convert module source to GitHub URL with caching."""
        if not self.source_url:
            raise ValueError("Source URL is required")
        
        # Clean up GitHub URLs that include tree/branch references
        if '/tree/' in self.source_url:
            # Extract the repository URL and branch
            repo_url, branch = self.source_url.split('/tree/')
            self.ref = branch.split('/')[0]  # Set the ref to the branch
            return repo_url
        
        if self.source_url.startswith(('http://', 'https://', 'git@')):
            return self.source_url.rstrip('/')

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

    def _parse_providers(self, file_path: str) -> Set[str]:
        """Parse provider blocks from a Terraform file."""
        providers = set()
        try:
            result = subprocess.run(
                ['/usr/local/bin/hcl2json', file_path],
                capture_output=True,
                text=True,
                check=True,
                timeout=10
            )
            
            tf_json = json.loads(result.stdout)
            
            # Check terraform required_providers block
            if 'terraform' in tf_json:
                terraform_block = tf_json['terraform']
                if isinstance(terraform_block, list):
                    terraform_block = terraform_block[0]
                required_providers = terraform_block.get('required_providers', {})
                if required_providers:
                    if isinstance(required_providers, dict):
                        # Handle nested provider configurations
                        for provider_name, provider_config in required_providers.items():
                            if isinstance(provider_config, dict):
                                # Get the actual provider type from source
                                source = provider_config.get('source', '')
                                if '/' in source:
                                    provider_type = source.split('/')[-1]
                                    if provider_type in ['aws', 'github']:
                                        providers.add(provider_type)
                                elif provider_name in ['aws', 'github']:
                                    providers.add(provider_name)
                            elif provider_name in ['aws', 'github']:
                                providers.add(provider_name)

            # Check direct provider blocks
            if 'provider' in tf_json:
                provider_blocks = tf_json['provider']
                if isinstance(provider_blocks, dict):
                    for provider_name in provider_blocks.keys():
                        base_provider = provider_name.split('.')[0]  # Handle provider.alias syntax
                        if base_provider in ['aws', 'github']:
                            providers.add(base_provider)
                elif isinstance(provider_blocks, list):
                    for block in provider_blocks:
                        for provider_name in block.keys():
                            base_provider = provider_name.split('.')[0]
                            if base_provider in ['aws', 'github']:
                                providers.add(base_provider)

        except Exception as e:
            logger.warning(f"Failed to parse providers from {file_path}: {str(e)}")

        return providers

    def get_provider_requirements(self) -> Tuple[List[str], List[FileSpec]]:
        """Get required environment variables and file mounts based on detected providers."""
        required_env = []
        required_files = []

        # Add provider-specific requirements
        for provider in self.providers:
            if provider in self.PROVIDER_REQUIREMENTS:
                config = self.PROVIDER_REQUIREMENTS[provider]
                required_env.extend(config['env'])
                required_files.extend(config['files'])

        # Remove duplicates while preserving order
        seen_env = set()
        unique_env = [x for x in required_env if not (x in seen_env or seen_env.add(x))]

        seen_files = set()
        unique_files = []
        for file in required_files:
            file_key = (file.source, file.destination)
            if file_key not in seen_files:
                seen_files.add(file_key)
                unique_files.append(file)

        return unique_env, unique_files

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
                # Parse variables
                var_futures = {
                    executor.submit(self._parse_variables_file, tf_file): tf_file
                    for tf_file in tf_files
                }
                
                # Parse providers
                provider_futures = {
                    executor.submit(self._parse_providers, tf_file): tf_file
                    for tf_file in tf_files
                }
                
                # Collect variables
                for future in as_completed(var_futures):
                    tf_file = var_futures[future]
                    try:
                        vars_in_file = future.result()
                        variables.update(vars_in_file)
                    except Exception as e:
                        logger.error(f"Failed to process variables in {tf_file}: {str(e)}")

                # Collect providers
                for future in as_completed(provider_futures):
                    tf_file = provider_futures[future]
                    try:
                        providers_in_file = future.result()
                        self.providers.update(providers_in_file)
                    except Exception as e:
                        logger.error(f"Failed to process providers in {tf_file}: {str(e)}")

        except Exception as e:
            logger.error(f"Failed to get variables and providers: {str(e)}", exc_info=True)
            self.errors.append(f"Failed to get variables and providers: {str(e)}")
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