import os
import json
import tempfile
import subprocess
import hcl2
import requests
from typing import Dict, Any, Optional, Tuple, List
from pathlib import Path
import logging
import re
import time
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)

class TerraformModuleScanner:
    def __init__(self):
        self.temp_dir = None
        self.registry_cache = {}
        self.cache_dir = Path.home() / '.terraform-scanner-cache'
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_retries = 3
        self.retry_delay = 2  # seconds

    def _get_cache_key(self, source: str, ref: Optional[str] = None) -> str:
        """Generate a unique cache key for a module."""
        key = f"{source}:{ref if ref else 'latest'}"
        return hashlib.sha256(key.encode()).hexdigest()

    def _load_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Load module data from cache."""
        cache_file = self.cache_dir / f"{cache_key}.json"
        if cache_file.exists():
            try:
                with open(cache_file) as f:
                    data = json.load(f)
                # Check if cache is still valid (24 hours)
                if time.time() - data.get('cached_at', 0) < 86400:
                    return data.get('content')
            except Exception as e:
                logger.debug(f"Cache read error: {e}")
        return None

    def _save_to_cache(self, cache_key: str, data: Dict[str, Any]):
        """Save module data to cache."""
        try:
            cache_file = self.cache_dir / f"{cache_key}.json"
            with open(cache_file, 'w') as f:
                json.dump({
                    'cached_at': time.time(),
                    'content': data
                }, f)
        except Exception as e:
            logger.debug(f"Cache write error: {e}")

    def _retry_operation(self, operation, *args, **kwargs):
        """Retry an operation with exponential backoff."""
        for attempt in range(self.max_retries):
            try:
                return operation(*args, **kwargs)
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise
                wait_time = self.retry_delay * (2 ** attempt)
                logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s...")
                time.sleep(wait_time)

    def _scan_file_safely(self, file_path: str) -> Dict[str, Any]:
        """Safely scan a file with multiple parsing attempts."""
        try:
            with open(file_path, 'r') as f:
                content = f.read()

            # Try different parsing strategies
            try:
                # First try: Direct HCL parsing
                return self._parse_hcl(content)
            except Exception as e1:
                try:
                    # Second try: Clean up the content
                    cleaned_content = self._cleanup_hcl(content)
                    return self._parse_hcl(cleaned_content)
                except Exception as e2:
                    # Third try: Parse line by line
                    return self._parse_line_by_line(content)
        except Exception as e:
            logger.warning(f"Failed to scan file {file_path}: {e}")
            return {"variables": {}, "outputs": {}, "providers": set()}

    def _cleanup_hcl(self, content: str) -> str:
        """Clean up HCL content for better parsing."""
        # Remove comments
        content = re.sub(r'(?m)^\s*#.*\n?', '', content)
        content = re.sub(r'//.*?\n', '\n', content)
        content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
        
        # Normalize whitespace
        content = re.sub(r'\n\s*\n', '\n\n', content)
        
        return content.strip()

    def _parse_line_by_line(self, content: str) -> Dict[str, Any]:
        """Parse HCL content line by line for maximum reliability."""
        results = {
            "variables": {},
            "outputs": {},
            "providers": set()
        }
        
        current_block = None
        current_name = None
        current_content = []
        
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith(('#', '//')):
                continue
                
            # Detect block starts
            if re.match(r'^(variable|output|provider)\s+"([^"]+)"\s*{', line):
                match = re.match(r'^(variable|output|provider)\s+"([^"]+)"\s*{', line)
                current_block = match.group(1)
                current_name = match.group(2)
                current_content = []
                
            # Detect block ends
            elif line == '}' and current_block:
                block_content = '\n'.join(current_content)
                
                if current_block == 'variable':
                    results['variables'][current_name] = self._parse_variable_content(block_content)
                elif current_block == 'output':
                    results['outputs'][current_name] = self._parse_output_content(block_content)
                elif current_block == 'provider':
                    results['providers'].add(current_name)
                    
                current_block = None
                current_name = None
                current_content = []
                
            # Collect block content
            elif current_block:
                current_content.append(line)
                
        return results

    def _parse_variable_content(self, content: str) -> Dict[str, Any]:
        """Parse variable block content."""
        var_info = {
            "type": "string",
            "description": "",
            "default": None,
            "required": True,
            "sensitive": False
        }
        
        # Extract type
        type_match = re.search(r'type\s*=\s*([a-zA-Z]+)', content)
        if type_match:
            var_info["type"] = type_match.group(1)
            
        # Extract description
        desc_match = re.search(r'description\s*=\s*"([^"]*)"', content)
        if desc_match:
            var_info["description"] = desc_match.group(1)
            
        # Check for default value
        if 'default' in content:
            var_info["required"] = False
            
        # Check for sensitive flag
        if 'sensitive = true' in content:
            var_info["sensitive"] = True
            
        return var_info

    def _parse_output_content(self, content: str) -> Dict[str, Any]:
        """Parse output block content."""
        return {
            "description": re.search(r'description\s*=\s*"([^"]*)"', content).group(1) if re.search(r'description\s*=\s*"([^"]*)"', content) else "",
            "sensitive": 'sensitive = true' in content
        }

    def _create_temp_dir(self):
        """Create a temporary directory for module scanning."""
        self.temp_dir = tempfile.mkdtemp(prefix="tf-scanner-")
        return self.temp_dir

    def _cleanup(self):
        """Clean up temporary files."""
        if self.temp_dir and os.path.exists(self.temp_dir):
            subprocess.run(["rm", "-rf", self.temp_dir], check=True)

    def _extract_type_info(self, type_str: str) -> Tuple[str, Optional[str]]:
        """Extract type and subtype from a Terraform type string."""
        if isinstance(type_str, dict):
            if 'type' in type_str:
                base_type = type_str['type']
                if base_type == 'list' or base_type == 'set':
                    return base_type, self._extract_type_info(type_str.get('items', 'string'))[0]
                elif base_type == 'map':
                    return base_type, self._extract_type_info(type_str.get('elem', 'string'))[0]
                return base_type, None
        return str(type_str), None

    def _parse_variable_block(self, var_config: Dict) -> Dict[str, Any]:
        """Parse a variable block and extract detailed type information."""
        type_str = var_config.get('type', 'string')
        base_type, sub_type = self._extract_type_info(type_str)
        
        # Handle validation rules
        validation_rules = []
        if 'validation' in var_config:
            for validation in var_config['validation']:
                if 'condition' in validation:
                    validation_rules.append({
                        'condition': validation['condition'],
                        'error_message': validation.get('error_message', '')
                    })

        # Extract examples from description if available
        description = var_config.get('description', '')
        examples = []
        if 'Example:' in description:
            example_matches = re.findall(r'Example:[\s\n]*`([^`]+)`', description)
            examples.extend(example_matches)

        return {
            "type": base_type,
            "sub_type": sub_type,
            "description": description,
            "default": var_config.get('default'),
            "required": 'default' not in var_config,
            "sensitive": var_config.get('sensitive', False),
            "validation": validation_rules,
            "examples": examples
        }

    def _scan_hcl_file(self, file_path: str) -> Dict[str, Any]:
        """Scan a single HCL file for variable definitions."""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Parse HCL content
            parsed = hcl2.loads(content)
            
            # Extract variables and outputs
            variables = {}
            outputs = {}
            
            if 'variable' in parsed:
                for var in parsed['variable']:
                    for var_name, var_config in var.items():
                        variables[var_name] = self._parse_variable_block(var_config)
            
            if 'output' in parsed:
                for out in parsed['output']:
                    for out_name, out_config in out.items():
                        outputs[out_name] = {
                            "description": out_config.get('description', ''),
                            "sensitive": out_config.get('sensitive', False)
                        }
            
            return {
                "variables": variables,
                "outputs": outputs
            }
        except Exception as e:
            logger.warning(f"Error scanning file {file_path}: {str(e)}")
            return {"variables": {}, "outputs": {}}

    def _get_readme_examples(self, module_path: str) -> List[Dict[str, Any]]:
        """Extract example configurations from README files."""
        examples = []
        readme_files = ['README.md', 'readme.md', 'USAGE.md', 'docs/README.md']
        
        for readme in readme_files:
            readme_path = os.path.join(module_path, readme)
            if os.path.exists(readme_path):
                with open(readme_path, 'r') as f:
                    content = f.read()
                
                # Find terraform code blocks
                code_blocks = re.findall(r'```(?:terraform|hcl)(.*?)```', content, re.DOTALL)
                for block in code_blocks:
                    try:
                        parsed = hcl2.loads(block)
                        if 'module' in parsed:
                            examples.append({
                                "name": "Example from README",
                                "code": block.strip(),
                                "variables": parsed.get('variable', {})
                            })
                    except:
                        continue
        
        return examples

    def scan_git_module(self, url: str, ref: Optional[str] = None, path: Optional[str] = None) -> Dict[str, Any]:
        """Scan a Git repository for Terraform variables with improved reliability."""
        cache_key = self._get_cache_key(url, ref)
        cached_data = self._load_from_cache(cache_key)
        if cached_data:
            return cached_data

        try:
            work_dir = self._create_temp_dir()
            
            # Clone repository with retries
            def clone_repo():
                clone_cmd = ["git", "clone", "--depth", "1"]
                if ref:
                    clone_cmd.extend(["--branch", ref])
                clone_cmd.extend([url, work_dir])
                subprocess.run(clone_cmd, check=True, capture_output=True)

            self._retry_operation(clone_repo)
            
            # Set module path
            module_path = os.path.join(work_dir, path) if path else work_dir
            
            results = {
                "variables": {},
                "outputs": {},
                "examples": [],
                "dependencies": set(),
                "providers": set(),
                "source": {
                    "type": "git",
                    "url": url,
                    "ref": ref,
                    "path": path
                }
            }
            
            # Parallel file scanning
            def scan_file(file_path: str):
                return file_path, self._scan_file_safely(file_path)

            tf_files = []
            for root, _, files in os.walk(module_path):
                for file in files:
                    if file.endswith('.tf'):
                        tf_files.append(os.path.join(root, file))

            with ThreadPoolExecutor(max_workers=min(len(tf_files), 5)) as executor:
                future_to_file = {executor.submit(scan_file, f): f for f in tf_files}
                for future in as_completed(future_to_file):
                    try:
                        file_path, scan_result = future.result()
                        results["variables"].update(scan_result["variables"])
                        results["outputs"].update(scan_result["outputs"])
                        results["providers"].update(scan_result.get("providers", set()))
                    except Exception as e:
                        logger.warning(f"Error scanning file {future_to_file[future]}: {e}")

            # Get examples from README
            results["examples"] = self._get_readme_examples(module_path)
            
            # Convert sets to lists for JSON serialization
            results["providers"] = list(results["providers"])
            results["dependencies"] = list(results["dependencies"])
            
            # Cache the results
            self._save_to_cache(cache_key, results)
            
            return results
            
        except Exception as e:
            logger.error(f"Error scanning git module: {str(e)}")
            raise
        finally:
            self._cleanup()

    def scan_registry_module(self, source: str) -> Dict[str, Any]:
        """Scan a registry module with improved reliability."""
        cache_key = self._get_cache_key(source)
        cached_data = self._load_from_cache(cache_key)
        if cached_data:
            return cached_data

        try:
            parts = source.split('/')
            if len(parts) < 3:
                raise ValueError(f"Invalid registry source: {source}")
            
            namespace, name, provider = parts[-3:]
            
            def fetch_module_data():
                base_url = "https://registry.terraform.io/v1/modules"
                module_url = f"{base_url}/{namespace}/{name}/{provider}"
                versions_url = f"{module_url}/versions"
                
                module_response = requests.get(module_url)
                versions_response = requests.get(versions_url)
                
                if module_response.status_code != 200 or versions_response.status_code != 200:
                    raise ValueError(f"Failed to fetch module data: {module_response.text}")
                
                return module_response.json(), versions_response.json()

            module_data, versions_data = self._retry_operation(fetch_module_data)
            
            result = {
                "variables": {},
                "outputs": {},
                "versions": [v["version"] for v in versions_data.get("modules", [])],
                "providers": module_data.get("provider_dependencies", []),
                "examples": [],
                "source": {
                    "type": "registry",
                    "namespace": namespace,
                    "name": name,
                    "provider": provider
                }
            }
            
            # Process variables with validation
            for var in module_data.get('variables', []):
                var_name = var.get('name')
                if not var_name:
                    continue
                    
                result["variables"][var_name] = {
                    "type": var.get('type', 'string'),
                    "description": var.get('description', ''),
                    "default": var.get('default'),
                    "required": var.get('required', True),
                    "sensitive": var.get('sensitive', False)
                }
            
            # Process outputs
            for output in module_data.get('outputs', []):
                output_name = output.get('name')
                if not output_name:
                    continue
                    
                result["outputs"][output_name] = {
                    "description": output.get('description', ''),
                    "sensitive": output.get('sensitive', False)
                }
            
            # Cache the result
            self._save_to_cache(cache_key, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error scanning registry module: {str(e)}")
            raise

    def scan_module(self, source_type: str, source_url: str, ref: Optional[str] = None, path: Optional[str] = None) -> Dict[str, Any]:
        """Scan a Terraform module with automatic retries and caching."""
        try:
            if source_type == "git":
                return self.scan_git_module(source_url, ref, path)
            elif source_type == "registry":
                return self.scan_registry_module(source_url)
            else:
                raise ValueError(f"Unsupported source type: {source_type}")
        except Exception as e:
            logger.error(f"Failed to scan module: {e}")
            # Return empty structure as fallback
            return {
                "variables": {},
                "outputs": {},
                "examples": [],
                "providers": [],
                "dependencies": [],
                "source": {
                    "type": source_type,
                    "url": source_url,
                    "ref": ref,
                    "path": path
                }
            }

__all__ = ['TerraformModuleScanner'] 