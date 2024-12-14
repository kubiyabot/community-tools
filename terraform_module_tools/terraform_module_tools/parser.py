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
from urllib.parse import urlparse, unquote

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

class ModuleSource:
    """Class to handle different types of module sources."""
    
    REGISTRY_DOMAIN = "registry.terraform.io"
    
    def __init__(self, source: str, version: Optional[str] = None):
        self.original_source = source
        self.version = version
        self.source_type = self._detect_source_type()
        self.parsed_source = self._parse_source()
    
    def _detect_source_type(self) -> str:
        """Detect the type of module source."""
        source = self.original_source.lower()
        
        if source.startswith(('http://', 'https://', 'git@')):
            if 'github.com' in source:
                return 'github'
            return 'git'
            
        if source.startswith(('aws://', 'azurerm://', 'google://')):
            return 'cloud'
            
        if '/' in source and len(source.split('/')) >= 2:
            # Check if it's a registry source
            if self.REGISTRY_DOMAIN in source:
                return 'registry'
            # Shorthand for registry modules
            if source.count('/') == 2:  # namespace/name/provider format
                return 'registry'
                
        return 'local'
    
    def _parse_source(self) -> Dict[str, Any]:
        """Parse the source string based on its type."""
        if self.source_type == 'github':
            return self._parse_github_source()
        elif self.source_type == 'registry':
            return self._parse_registry_source()
        elif self.source_type == 'git':
            return self._parse_git_source()
        elif self.source_type == 'cloud':
            return self._parse_cloud_source()
        else:
            return self._parse_local_source()
    
    def _parse_github_source(self) -> Dict[str, Any]:
        """Parse GitHub repository source."""
        source = self.original_source
        
        # Handle tree references
        ref = self.version or 'master'
        path = None
        
        if '/tree/' in source:
            base_url, tree_part = source.split('/tree/', 1)
            parts = tree_part.split('/', 1)
            ref = parts[0]
            path = parts[1] if len(parts) > 1 else None
            source = base_url
            
        # Clean up the URL
        if source.startswith('git@github.com:'):
            source = f"https://github.com/{source[15:]}"
        
        # Remove .git suffix if present
        source = source.rstrip('.git')
        
        return {
            'url': source,
            'ref': ref,
            'path': path,
            'clone_url': f"{source}.git"
        }
    
    def _parse_registry_source(self) -> Dict[str, Any]:
        """Parse Terraform registry source."""
        parts = self.original_source.split('/')
        
        if self.REGISTRY_DOMAIN in self.original_source:
            # Handle full registry URLs
            if len(parts) >= 5:  # registry.terraform.io/namespace/name/provider
                namespace, name, provider = parts[-3:]
            else:
                raise ValueError(f"Invalid registry source format: {self.original_source}")
        else:
            # Handle shorthand format (namespace/name/provider)
            if len(parts) == 3:
                namespace, name, provider = parts
            else:
                raise ValueError(f"Invalid registry source format: {self.original_source}")
        
        return {
            'namespace': namespace,
            'name': name,
            'provider': provider,
            'version': self.version,
            'url': f"https://{self.REGISTRY_DOMAIN}/{namespace}/{name}/{provider}"
        }
    
    def _parse_git_source(self) -> Dict[str, Any]:
        """Parse generic Git repository source."""
        url = self.original_source
        ref = self.version or 'master'
        
        # Convert SSH to HTTPS if needed
        if url.startswith('git@'):
            domain = url[4:url.index(':')]
            path = url[url.index(':')+1:]
            url = f"https://{domain}/{path}"
        
        return {
            'url': url.rstrip('.git'),
            'ref': ref,
            'clone_url': url
        }
    
    def _parse_cloud_source(self) -> Dict[str, Any]:
        """Parse cloud-specific source."""
        scheme, path = self.original_source.split('://', 1)
        provider = scheme.lower()
        
        return {
            'provider': provider,
            'path': path,
            'version': self.version
        }
    
    def _parse_local_source(self) -> Dict[str, Any]:
        """Parse local filesystem source."""
        return {
            'path': os.path.abspath(self.original_source),
            'version': self.version
        }
    
    def get_clone_url(self) -> str:
        """Get the URL to clone the repository."""
        if self.source_type == 'github':
            return self.parsed_source['clone_url']
        elif self.source_type == 'git':
            return self.parsed_source['clone_url']
        elif self.source_type == 'registry':
            # For registry modules, we need to get the source from the registry
            registry_client = TerraformRegistryClient()
            module_source = registry_client.get_module_source(
                self.parsed_source['namespace'],
                self.parsed_source['name'],
                self.parsed_source['provider'],
                self.parsed_source['version']
            )
            return module_source
        
        raise ValueError(f"Source type {self.source_type} does not support cloning")
    
    def get_ref(self) -> Optional[str]:
        """Get the reference (branch, tag, commit) to checkout."""
        if self.source_type in ('github', 'git'):
            return self.parsed_source['ref']
        return None
    
    def get_path(self) -> Optional[str]:
        """Get the path within the repository."""
        if self.source_type == 'github':
            return self.parsed_source.get('path')
        return None

class TerraformRegistryClient:
    """Client for interacting with Terraform Registry API."""
    
    def __init__(self):
        self.base_url = "https://registry.terraform.io/v1"
        
    def get_module_source(self, namespace: str, name: str, provider: str, version: Optional[str] = None) -> str:
        """Get the source URL for a registry module."""
        try:
            # Get latest version if not specified
            if not version:
                versions_url = f"{self.base_url}/modules/{namespace}/{name}/{provider}/versions"
                response = requests.get(versions_url)
                response.raise_for_status()
                versions = response.json()['modules'][0]['versions']
                version = versions[0]['version']
            
            # Get download URL
            download_url = f"{self.base_url}/modules/{namespace}/{name}/{provider}/{version}/download"
            response = requests.get(download_url)
            response.raise_for_status()
            
            # Registry returns a redirect to the actual source
            return response.headers['X-Terraform-Get']
            
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Failed to get module source from registry: {str(e)}")

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
        max_workers: int = 4
    ):
        self.source = ModuleSource(source_url, version=ref)
        self.path = path or self.source.get_path()
        self.warnings = []
        self.errors = []
        self.readme_url = None
        self.module_dir = None
        self.max_workers = max_workers
        self.providers: Set[str] = set()
        self._clone_repository()
        ensure_hcl2json()

    def _clone_repository(self) -> None:
        """Clone the repository with optimized git operations."""
        temp_dir = tempfile.mkdtemp()

        try:
            logger.info(f"Cloning repository from {self.source.get_clone_url()}")
            
            clone_cmd = ['git', 'clone', '--depth', '1', '--single-branch']
            
            if ref := self.source.get_ref():
                clone_cmd.extend(['--branch', ref])
            
            clone_url = self.source.get_clone_url()
            
            # Handle GitHub authentication tokens
            if 'github.com' in clone_url:
                # Try GH_TOKEN first, then TOOLS_GH_TOKEN
                github_token = os.environ.get('GH_TOKEN') or os.environ.get('TOOLS_GH_TOKEN')
                if github_token:
                    logger.debug("Using GitHub token for authentication")
                    auth_url = clone_url.replace(
                        "https://github.com",
                        f"https://{github_token}@github.com"
                    )
                    clone_cmd.append(auth_url)
                else:
                    logger.debug("No GitHub token found, using unauthenticated access")
                    clone_cmd.append(clone_url)
            else:
                clone_cmd.append(clone_url)
            
            clone_cmd.append(str(temp_dir))
            
            # Run git clone command
            try:
                result = subprocess.run(
                    clone_cmd, 
                    check=True, 
                    capture_output=True,
                    text=True,
                    env={**os.environ, 'GIT_TERMINAL_PROMPT': '0'}  # Prevent git from prompting for credentials
                )
            except subprocess.CalledProcessError as e:
                error_msg = f"Git clone failed: {e.stderr}"
                if 'Authentication failed' in e.stderr:
                    error_msg = "GitHub authentication failed. Please ensure either GH_TOKEN or TOOLS_GH_TOKEN is set with valid credentials."
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            # Set the module directory
            self.module_dir = os.path.join(temp_dir, self.path or '')
            if self.path and not os.path.exists(self.module_dir):
                raise ValueError(f"Specified path '{self.path}' does not exist")

            # Set README URL for GitHub repositories
            if self.source.source_type == 'github':
                base_url = self.source.parsed_source['url']
                ref = self.source.get_ref() or 'master'
                path = self.source.get_path() or ''
                self.readme_url = f"{base_url}/blob/{ref}/{path}/README.md".rstrip('/')

        except subprocess.CalledProcessError as e:
            error_msg = f"Failed to clone repository: {e.stderr}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        except Exception as e:
            error_msg = f"Failed to clone repository: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        finally:
            # Ensure we don't leave the token in the error messages
            if 'github_token' in locals():
                for handler in logger.handlers:
                    handler.formatter._fmt = handler.formatter._fmt.replace(github_token, '***')

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