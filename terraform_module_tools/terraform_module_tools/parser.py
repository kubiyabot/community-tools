import os
import json
import tempfile
import subprocess
from typing import Dict, Any, List, Optional, Tuple, Set, Union
import logging
import re
import glob
import shutil
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
from kubiya_sdk.tools.models import FileSpec
from urllib.parse import urlparse, unquote
from pathlib import Path

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
        self._source_type = None
        self._parsed_source = None
    
    @property
    @lru_cache(maxsize=1)
    def source_type(self) -> str:
        """Cached source type detection."""
        if self._source_type is None:
            self._source_type = self._detect_source_type()
        return self._source_type
    
    @property
    @lru_cache(maxsize=1)
    def parsed_source(self) -> Dict[str, Any]:
        """Cached source parsing."""
        if self._parsed_source is None:
            self._parsed_source = self._parse_source()
        return self._parsed_source

    @lru_cache(maxsize=1)
    def get_clone_url(self) -> str:
        """Cached clone URL generation."""
        if self.source_type == 'registry':
            return self.parsed_source['clone_url']
        elif self.source_type in ('github', 'git'):
            return self.parsed_source['clone_url']
        raise ValueError(f"Source type {self.source_type} does not support cloning")
    
    def _detect_source_type(self) -> str:
        """Detect the type of module source."""
        source = self.original_source.lower()
        
        # Handle GitHub variations
        if any(pattern in source for pattern in [
            'github.com', 
            'git@github.com:', 
            'git::https://github.com',
            'github.com/tree'
        ]):
            return 'github'
            
        # Handle other Git sources
        if any(pattern in source for pattern in [
            'gitlab.com',
            'bitbucket.org',
            'git::', 
            'git@',
            '.git'
        ]):
            return 'git'
            
        # Handle cloud sources
        if source.startswith((
            'aws://', 
            'azurerm://', 
            'google://',
            'oci://',
            'alicloud://'
        )):
            return 'cloud'
            
        # Handle registry sources
        if '/' in source and len(source.split('/')) >= 2:
            if self.REGISTRY_DOMAIN in source:
                return 'registry'
            if source.count('/') == 2:  # namespace/name/provider format
                return 'registry'
                
        # Handle local paths and other formats
        if (
            source.startswith(('./', '../', '/')) or
            ':' not in source or
            source.startswith('file://')
        ):
            return 'local'
            
        return 'unknown'
    
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
        """Parse GitHub repository source with all variations."""
        source = self.original_source
        ref = self.version or 'master'
        path = None
        
        # Remove git:: prefix if present
        if source.startswith('git::'):
            source = source[5:]
            
        # Handle tree references and subpaths
        if '/tree/' in source:
            base_url, tree_part = source.split('/tree/', 1)
            parts = tree_part.split('/', 1)
            ref = parts[0]
            path = parts[1] if len(parts) > 1 else None
            source = base_url
            
        # Handle SSH format
        if source.startswith('git@github.com:'):
            source = f"https://github.com/{source[15:]}"
            
        # Handle various URL formats
        if '?ref=' in source:
            source, ref_part = source.split('?ref=', 1)
            ref = ref_part.split('&')[0]
            
        # Clean up the URL
        source = source.rstrip('/')
        if source.endswith('.git'):
            source = source[:-4]
            
        # Ensure HTTPS format
        if not source.startswith('http'):
            if source.startswith('github.com/'):
                source = f"https://{source}"
            elif source.startswith('/'):
                source = f"https://github.com{source}"
                
        return {
            'url': source,
            'ref': ref,
            'path': path,
            'clone_url': f"{source}.git"
        }
    
    def _parse_registry_source(self) -> Dict[str, Any]:
        """Parse Terraform registry source."""
        parts = self.original_source.split('/')
        
        # Handle various registry formats
        if self.REGISTRY_DOMAIN in self.original_source:
            # Full registry URLs
            if len(parts) >= 5:  # registry.terraform.io/namespace/name/provider
                namespace, name, provider = parts[-3:]
            else:
                raise ValueError(f"Invalid registry format: {self.original_source}")
        else:
            # Short format (hashicorp/consul/aws)
            if len(parts) == 3:
                namespace, name, provider = parts
            else:
                raise ValueError(f"Invalid registry format: {self.original_source}")
        
        # Construct GitHub URL for the module
        github_url = f"https://github.com/terraform-aws-modules/terraform-{provider}-{name}"
        
        return {
            'namespace': namespace,
            'name': name,
            'provider': provider,
            'version': self.version,
            'url': github_url,
            'clone_url': f"{github_url}.git"
        }
    
    def _parse_git_source(self) -> Dict[str, Any]:
        """Parse generic Git repository source."""
        url = self.original_source
        ref = self.version or 'master'
        path = None
        
        # Handle git:: prefix
        if url.startswith('git::'):
            url = url[5:]
            
        # Handle ref in URL
        if '?ref=' in url:
            url, ref_part = url.split('?ref=', 1)
            ref = ref_part.split('&')[0]
            
        # Handle SSH format
        if url.startswith('git@'):
            domain = url[4:url.index(':')]
            path = url[url.index(':')+1:]
            url = f"https://{domain}/{path}"
            
        # Handle subpaths
        if '//' in url:
            url, path = url.split('//', 1)
            
        return {
            'url': url.rstrip('.git'),
            'ref': ref,
            'path': path,
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

    def get_module_name(self) -> str:
        """Get a clean module name for tool creation."""
        if self.source_type == 'github':
            # Extract name from GitHub URL
            name = self.parsed_source['url'].split('/')[-1]
            if name.startswith('terraform-'):
                # Handle terraform-provider-resource format
                parts = name.split('-')
                if len(parts) >= 3:
                    provider = parts[1]
                    resource = '_'.join(parts[2:])
                    return f"{provider}_{resource}"
            return name.replace('-', '_')
            
        elif self.source_type == 'registry':
            # Use provider_name format for registry modules
            return f"{self.parsed_source['provider']}_{self.parsed_source['name']}"
            
        elif self.source_type == 'git':
            # Extract name from Git URL
            name = self.parsed_source['url'].split('/')[-1].replace('.git', '')
            return name.replace('-', '_')
            
        else:
            # For other sources, use a sanitized version of the path
            name = os.path.basename(self.original_source)
            return re.sub(r'[^\w_]', '', name).lower()

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

    # Add class-level cache for git installation check
    _git_installed = False

    # Add class-level thread pool for reuse
    _executor = ThreadPoolExecutor(max_workers=os.cpu_count() or 4)

    @classmethod
    def _ensure_git(cls):
        """Ensure git is installed (cached)."""
        if cls._git_installed:
            return
        
        try:
            subprocess.run(['git', '--version'], check=True, capture_output=True)
            cls._git_installed = True
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.info("Installing git and required packages...")
            subprocess.run(['apk', 'add', '--no-cache', 'git', 'git-remote-https'], check=True)
            cls._git_installed = True

    def __init__(
        self,
        source_url: str,
        ref: Optional[str] = None,
        path: Optional[str] = None,
        module_config: Optional[Dict[str, Any]] = None
    ):
        self.source = ModuleSource(source_url, version=ref)
        self.path = path or self.source.get_path()
        self.warnings = []
        self.errors = []
        self.readme_url = None
        self.module_dir = None
        self.providers: Set[str] = set()
        self.module_config = module_config
        
        # Clone and initialize in parallel
        future_clone = self._executor.submit(self._clone_repository)
        future_hcl = self._executor.submit(ensure_hcl2json) if not module_config or module_config.get('auto_discover', True) else None

        # Wait for initialization
        try:
            future_clone.result()
            if future_hcl:
                future_hcl.result()
        except Exception as e:
            raise ValueError(f"Failed to initialize: {str(e)}")

    def _clone_repository(self) -> None:
        """Optimized repository cloning."""
        temp_dir = tempfile.mkdtemp()

        try:
            # Ensure git is installed (cached)
            self._ensure_git()

            # Get clone URL from source
            clone_url = self.source.get_clone_url()
            logger.info(f"Using clone URL: {clone_url}")
            
            # Prepare command list efficiently
            clone_cmd = ['git', 'clone', '--depth', '1', '--single-branch']
            if ref := self.source.get_ref():
                clone_cmd.extend(['--branch', ref])

            # Handle auth token once
            if 'github.com' in clone_url:
                github_token = os.environ.get('GH_TOKEN') or os.environ.get('TOOLS_GH_TOKEN')
                if github_token:
                    clone_url = clone_url.replace(
                        "https://github.com",
                        f"https://{github_token}@github.com"
                    )

            clone_cmd.extend([clone_url, str(temp_dir)])
            
            # Single subprocess call with prepared command
            try:
                result = subprocess.run(
                    clone_cmd, 
                    check=True, 
                    capture_output=True,
                    text=True,
                    env={'GIT_TERMINAL_PROMPT': '0', **os.environ}
                )
            except subprocess.CalledProcessError as e:
                raise ValueError(f"Git clone failed: {e.stderr}")

            # Set module directory efficiently
            self.module_dir = os.path.join(temp_dir, self.path or '')
            if self.path and not os.path.exists(self.module_dir):
                raise ValueError(f"Specified path '{self.path}' does not exist")

            # Set README URL for GitHub repositories
            if self.source.source_type in ('github', 'registry'):
                base_url = clone_url.rstrip('.git')
                ref = self.source.get_ref() or 'master'
                path = self.source.get_path() or ''
                self.readme_url = f"{base_url}/blob/{ref}/{path}/README.md".rstrip('/')

        except Exception as e:
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise ValueError(f"Failed to clone repository: {str(e)}")

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

    def get_variables_from_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Get variables from manual configuration."""
        if not config.get('variables'):
            return {}
            
        variables = {}
        for var_name, var_config in config['variables'].items():
            variables[var_name] = {
                'type': var_config.get('type', 'string'),
                'description': var_config.get('description', ''),
                'default': var_config.get('default'),
                'required': var_config.get('required', False)
            }
        return variables

    def get_variables(self) -> Tuple[Dict[str, Any], List[str], List[str]]:
        """Optimized parallel variable parsing."""
        try:
            if not self.module_dir:
                raise ValueError("Module directory not set. Module may not exist or failed to clone.")

            # Fast path for manual configuration
            if self.module_config and not self.module_config.get('auto_discover', True):
                # Quick validation of module existence
                if not any(Path(self.module_dir).glob('*.tf')):
                    self.errors.append("No .tf files found in module - module may not be valid")
                    return {}, self.warnings, self.errors

                variables = self.get_variables_from_config(self.module_config)
                self._set_providers_from_config()
                return variables, [], []

            # Collect files in parallel
            tf_files = list(Path(self.module_dir).rglob('*.tf'))
            if not tf_files:
                self.errors.append("No .tf files found in module")
                return {}, self.warnings, self.errors

            # Process files in parallel batches
            batch_size = 10
            variables = {}
            providers = set()
            
            for i in range(0, len(tf_files), batch_size):
                batch = tf_files[i:i + batch_size]
                futures = {
                    self._executor.submit(self._parse_file, tf_file): tf_file
                    for tf_file in batch
                }
                
                for future in as_completed(futures):
                    try:
                        file_vars, file_providers = future.result()
                        variables.update(file_vars)
                        providers.update(file_providers)
                    except Exception as e:
                        logger.error(f"Failed to process file: {str(e)}")

            self.providers = providers
            return variables, self.warnings, self.errors

        except Exception as e:
            logger.error(f"Failed to get variables: {str(e)}", exc_info=True)
            self.errors.append(f"Failed to get variables: {str(e)}")
            return {}, self.warnings, self.errors

    @lru_cache(maxsize=100)
    def _parse_file(self, file_path: str) -> Tuple[Dict[str, Any], Set[str]]:
        """Parse both variables and providers from a file with caching."""
        try:
            result = subprocess.run(
                ['/usr/local/bin/hcl2json', str(file_path)],
                capture_output=True,
                text=True,
                check=True,
                timeout=10
            )
            
            tf_json = json.loads(result.stdout)
            variables = {}
            providers = set()

            # Process variables
            if 'variable' in tf_json:
                try:
                    variables = self._process_variables(tf_json['variable'])
                except Exception as e:
                    logger.error(f"Failed to process variables in {file_path}: {str(e)}")

            # Process providers
            if 'provider' in tf_json:
                try:
                    providers.update(self._process_providers(tf_json['provider']))
                except Exception as e:
                    logger.error(f"Failed to process providers in {file_path}: {str(e)}")

            # Process required providers
            if 'terraform' in tf_json:
                try:
                    providers.update(self._process_required_providers(tf_json['terraform']))
                except Exception as e:
                    logger.error(f"Failed to process required providers in {file_path}: {str(e)}")

            return variables, providers

        except Exception as e:
            logger.error(f"Failed to parse {file_path}: {str(e)}")
            return {}, set()

    def _process_variables(self, var_blocks: Union[Dict[str, Any], List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Process variables with proper type handling."""
        variables = {}
        
        # Convert list format to dict format
        if isinstance(var_blocks, list):
            var_dict = {}
            for block in var_blocks:
                if isinstance(block, dict):
                    var_dict.update(block)
            var_blocks = var_dict

        # Process each variable
        for var_name, var_config in var_blocks.items():
            # Handle list format from HCL2JSON
            if isinstance(var_config, list):
                var_config = var_config[0] if var_config else {}
            
            # Skip if not a dict
            if not isinstance(var_config, dict):
                logger.warning(f"Skipping invalid variable config for {var_name}: {var_config}")
                continue

            try:
                # Extract type, default, and description
                var_type = var_config.get('type', 'string')
                if isinstance(var_type, (dict, list)):
                    # Handle complex types
                    var_type = json.dumps(var_type)
                
                description = var_config.get('description', '')
                if isinstance(description, (dict, list)):
                    description = json.dumps(description)

                # Handle default value
                default = var_config.get('default')
                if isinstance(default, (dict, list)):
                    default = json.dumps(default)

                variables[var_name] = {
                    'type': str(var_type),
                    'description': str(description),
                    'default': default,
                    'required': default is None
                }

            except Exception as e:
                logger.warning(f"Failed to process variable {var_name}: {str(e)}")
                continue

        return variables

    def _process_providers(self, provider_blocks: Union[Dict[str, Any], List[Dict[str, Any]]]) -> Set[str]:
        """Process provider blocks with proper type handling."""
        providers = set()
        
        # Handle both list and dict formats
        if isinstance(provider_blocks, list):
            for block in provider_blocks:
                if isinstance(block, dict):
                    providers.update(block.keys())
        elif isinstance(provider_blocks, dict):
            providers.update(provider_blocks.keys())
        
        return providers

    def _process_required_providers(self, terraform_block: Dict[str, Any]) -> Set[str]:
        """Process required_providers block with proper type handling."""
        providers = set()
        
        try:
            required_providers = terraform_block.get('required_providers', {})
            if isinstance(required_providers, list):
                required_providers = required_providers[0] if required_providers else {}
                
            if isinstance(required_providers, dict):
                providers.update(required_providers.keys())
        except Exception as e:
            logger.error(f"Failed to process required providers: {str(e)}")
        
        return providers