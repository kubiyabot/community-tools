import os
import json
import tempfile
import subprocess
import requests
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

HCL2JSON_BINARY = "hcl2json"
HCL2JSON_URL = "https://github.com/tmccombs/hcl2json/releases/download/v0.6.4/hcl2json_linux_amd64"

@dataclass
class TerraformType:
    """Represents a Terraform type with nested structure."""
    base_type: str
    nested_type: Optional['TerraformType'] = None
    object_attributes: Dict[str, 'TerraformType'] = field(default_factory=dict)
    example_value: Any = None

    def generate_example(self) -> Any:
        """Generate example value based on type."""
        if self.example_value is not None:
            return self.example_value

        if self.base_type == "string":
            return "example_value"
        elif self.base_type == "number":
            return 42
        elif self.base_type == "bool":
            return True
        elif self.base_type == "list":
            if self.nested_type:
                return [self.nested_type.generate_example()]
            return ["example"]
        elif self.base_type == "set":
            if self.nested_type:
                return [self.nested_type.generate_example()]
            return ["example"]
        elif self.base_type == "map":
            if self.nested_type:
                return {"key": self.nested_type.generate_example()}
            return {"key": "value"}
        elif self.base_type == "object":
            return {
                name: attr_type.generate_example()
                for name, attr_type in self.object_attributes.items()
            }
        return None

    def to_json_schema(self) -> Dict[str, Any]:
        """Convert to JSON schema for validation."""
        if self.base_type == "string":
            return {"type": "string"}
        elif self.base_type == "number":
            return {"type": "number"}
        elif self.base_type == "bool":
            return {"type": "boolean"}
        elif self.base_type in ["list", "set"]:
            return {
                "type": "array",
                "items": self.nested_type.to_json_schema() if self.nested_type else {"type": "string"}
            }
        elif self.base_type == "map":
            return {
                "type": "object",
                "additionalProperties": self.nested_type.to_json_schema() if self.nested_type else {"type": "string"}
            }
        elif self.base_type == "object":
            return {
                "type": "object",
                "properties": {
                    name: attr_type.to_json_schema()
                    for name, attr_type in self.object_attributes.items()
                },
                "required": [name for name, attr_type in self.object_attributes.items() if attr_type.required]
            }
        return {}

@dataclass
class TerraformVariable:
    name: str
    type: TerraformType
    description: Optional[str]
    default: Optional[Any]
    required: bool
    sensitive: bool = False
    validation_rules: List[Dict[str, str]] = field(default_factory=list)

    def get_example_value(self) -> str:
        """Get JSON-formatted example value with comments."""
        example = self.type.generate_example()
        if isinstance(example, (dict, list)):
            return json.dumps(example, indent=2)
        return str(example)

    def get_input_format(self) -> str:
        """Get human-readable input format description."""
        if self.type.base_type == "object":
            return (
                f"JSON object with the following structure:\n"
                f"{json.dumps(self.type.generate_example(), indent=2)}"
            )
        elif self.type.base_type in ["list", "set"]:
            return f"JSON array of {self.type.nested_type.base_type if self.type.nested_type else 'string'}s"
        elif self.type.base_type == "map":
            return f"JSON object with string keys and {self.type.nested_type.base_type if self.type.nested_type else 'string'} values"
        return self.type.base_type

def parse_terraform_type(type_str: str, type_info: Any = None) -> TerraformType:
    """Parse Terraform type string into TerraformType object."""
    if isinstance(type_str, str):
        if type_str.startswith("list(") or type_str.startswith("set("):
            inner_type = type_str[type_str.index("(") + 1:type_str.rindex(")")]
            return TerraformType(
                base_type="list" if type_str.startswith("list") else "set",
                nested_type=parse_terraform_type(inner_type)
            )
        elif type_str.startswith("map("):
            inner_type = type_str[4:-1]
            return TerraformType(
                base_type="map",
                nested_type=parse_terraform_type(inner_type)
            )
        return TerraformType(base_type=type_str)
    
    # Handle complex object types
    if isinstance(type_info, dict):
        attributes = {}
        for attr_name, attr_info in type_info.items():
            if isinstance(attr_info, dict) and "type" in attr_info:
                attributes[attr_name] = parse_terraform_type(
                    attr_info["type"],
                    attr_info.get("nested_type")
                )
        return TerraformType(base_type="object", object_attributes=attributes)
    
    return TerraformType(base_type="string")

class TerraformSourceError(Exception):
    """Base exception for Terraform source errors."""
    pass

class GitSourceError(TerraformSourceError):
    """Exception for Git-related errors."""
    pass

class ParsingError(TerraformSourceError):
    """Exception for HCL parsing errors."""
    pass

class ModuleWarning:
    """Warning during module parsing."""
    def __init__(self, module_path: str, message: str):
        self.module_path = module_path
        self.message = message

    def __str__(self):
        return f"⚠️ {self.module_path}: {self.message}"

class ModuleError:
    """Critical error during module parsing."""
    def __init__(self, module_path: str, error: str, details: Optional[str] = None):
        self.module_path = module_path
        self.error = error
        self.details = details

    def __str__(self):
        msg = f"❌ {self.module_path}: {self.error}"
        if self.details:
            msg += f"\n   Details: {self.details}"
        return msg

class TerraformModuleParser:
    def __init__(self, source_url: str, ref: Optional[str] = None, subfolder: Optional[str] = None):
        """
        Initialize Terraform module parser.
        
        Args:
            source_url: URL or path to Terraform module
                Supported formats:
                - GitHub: https://github.com/org/repo
                - GitLab: https://gitlab.com/org/repo
                - Local path: /path/to/module
                - S3: s3://bucket/path
                - HTTP(S): https://example.com/module.zip
            ref: Git reference (branch, tag, commit)
            subfolder: Path to module within repository
        """
        self.source_url = source_url
        self.ref = ref
        self.subfolder = subfolder
        self.warnings = []
        self.errors = []
        self._ensure_hcl2json()

    def add_warning(self, message: str):
        """Add a warning message."""
        self.warnings.append(ModuleWarning(self.source_url, message))

    def add_error(self, error: str, details: Optional[str] = None):
        """Add an error message."""
        self.errors.append(ModuleError(self.source_url, error, details))

    def _ensure_hcl2json(self) -> None:
        """Ensure hcl2json binary is available."""
        try:
            result = subprocess.run([HCL2JSON_BINARY, "--version"], 
                                  capture_output=True, 
                                  text=True,
                                  check=True)
            print(f"✅ hcl2json binary found: {result.stdout.strip()}")
        except (subprocess.SubprocessError, FileNotFoundError):
            print("⚙️ Downloading hcl2json binary...")
            try:
                response = requests.get(HCL2JSON_URL, timeout=30)
                response.raise_for_status()
                
                bin_path = "/usr/local/bin/hcl2json"
                with open(bin_path, 'wb') as f:
                    f.write(response.content)
                
                os.chmod(bin_path, 0o755)
                print("✅ hcl2json binary installed successfully")
            except Exception as e:
                raise RuntimeError(f"Failed to download hcl2json binary: {str(e)}")

    def _parse_hcl_file(self, file_path: str) -> Dict[str, Any]:
        """Parse HCL file using hcl2json binary."""
        try:
            result = subprocess.run(
                [HCL2JSON_BINARY, file_path],
                capture_output=True,
                text=True,
                check=True
            )
            return json.loads(result.stdout)
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.strip() if e.stderr else str(e)
            raise ParsingError(f"Failed to parse {file_path}: {error_msg}")
        except json.JSONDecodeError as e:
            raise ParsingError(f"Invalid JSON output for {file_path}: {str(e)}")

    def _get_source_type(self) -> Tuple[str, str]:
        """Determine source type and normalized URL/path."""
        url = urlparse(self.source_url)
        
        if url.scheme in ('http', 'https'):
            if any(domain in url.netloc for domain in ['github.com', 'gitlab.com']):
                return 'git', self.source_url
            return 'http', self.source_url
        elif url.scheme == 's3':
            return 's3', self.source_url
        elif url.scheme == 'git':
            return 'git', self.source_url
        elif os.path.exists(self.source_url):
            return 'local', os.path.abspath(self.source_url)
        else:
            raise TerraformSourceError(f"Unsupported or invalid source: {self.source_url}")

    def _clone_repo(self) -> Dict[str, TerraformVariable]:
        """Clone repository and parse variables."""
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                source_type, source_url = self._get_source_type()
                
                if source_type == 'git':
                    # Handle GitHub/GitLab authentication if token is present
                    auth_url = source_url
                    if "GH_TOKEN" in os.environ and "github.com" in source_url:
                        auth_url = source_url.replace(
                            "https://github.com",
                            f"https://{os.environ['GH_TOKEN']}@github.com"
                        )
                    elif "GL_TOKEN" in os.environ and "gitlab.com" in source_url:
                        auth_url = source_url.replace(
                            "https://gitlab.com",
                            f"https://oauth2:{os.environ['GL_TOKEN']}@gitlab.com"
                        )
                    
                    print(f"📦 Cloning repository {source_url}...")
                    
                    # Use git command line instead of gitpython
                    try:
                        subprocess.run(
                            ["git", "clone", auth_url, temp_dir],
                            check=True,
                            capture_output=True,
                            text=True
                        )
                        
                        if self.ref:
                            print(f"⚡ Checking out ref: {self.ref}")
                            subprocess.run(
                                ["git", "checkout", self.ref],
                                cwd=temp_dir,
                                check=True,
                                capture_output=True,
                                text=True
                            )
                    except subprocess.CalledProcessError as e:
                        raise GitSourceError(f"Git operation failed: {e.stderr}")
                    
                    module_path = temp_dir
                    if self.subfolder:
                        module_path = os.path.join(temp_dir, self.subfolder)
                        if not os.path.exists(module_path):
                            raise GitSourceError(f"Subfolder not found: {self.subfolder}")
                    
                    return self.parse_directory(module_path)
                else:
                    return self.parse_directory(source_url)
                    
            except Exception as e:
                raise TerraformSourceError(f"Failed to process source: {str(e)}")

    def parse_directory(self, directory: str) -> Dict[str, TerraformVariable]:
        """Parse all .tf files in directory and extract variables."""
        variables = {}
        critical_error = False
        
        try:
            for root, _, files in os.walk(directory):
                for file in files:
                    if file.endswith(('.tf', '.tf.json')):
                        file_path = os.path.join(root, file)
                        try:
                            tf_dict = self._parse_hcl_file(file_path)
                            if 'variable' in tf_dict:
                                for var_name, var_config in tf_dict['variable'].items():
                                    try:
                                        # Parse type information
                                        type_str = var_config.get('type', 'string')
                                        tf_type = parse_terraform_type(type_str, var_config.get('type_info'))

                                        # Parse validation rules
                                        validation_rules = []
                                        if 'validation' in var_config:
                                            for rule in var_config['validation']:
                                                validation_rules.append({
                                                    'condition': rule.get('condition', ''),
                                                    'error_message': rule.get('error_message', '')
                                                })

                                        variables[var_name] = TerraformVariable(
                                            name=var_name,
                                            type=tf_type,
                                            description=var_config.get('description'),
                                            default=var_config.get('default'),
                                            required='default' not in var_config,
                                            sensitive=var_config.get('sensitive', False),
                                            validation_rules=validation_rules
                                        )
                                    except Exception as e:
                                        self.add_warning(f"Failed to parse variable '{var_name}' in {file_path}: {str(e)}")

                        except ParsingError as e:
                            self.add_warning(f"Failed to parse {file_path}: {str(e)}")
                        except Exception as e:
                            self.add_error(f"Unexpected error parsing {file_path}", str(e))
                            critical_error = True
            
            if critical_error:
                print("\n🚨 Critical Errors:")
                for error in self.errors:
                    print(f"{error}")
                print("\nContinuing with partial results...\n")

            if self.warnings:
                print("\n⚠️ Warnings:")
                for warning in self.warnings:
                    print(f"{warning}")
            
            if not variables:
                self.add_warning("No variables found in module")
            else:
                print(f"\n✅ Successfully parsed {len(variables)} variables")
                print("\n📊 Variable Summary:")
                print(f"  Required: {sum(1 for v in variables.values() if v.required)}")
                print(f"  Optional: {sum(1 for v in variables.values() if not v.required)}")
                print(f"  Sensitive: {sum(1 for v in variables.values() if v.sensitive)}")
                print("\n🔍 Complex Types:")
                for name, var in variables.items():
                    if var.type.base_type in ['object', 'map', 'list', 'set']:
                        print(f"  - {name}: {var.get_input_format()}")
            
            return variables
            
        except Exception as e:
            self.add_error("Failed to parse directory", str(e))
            return {}

    def get_variables(self) -> Tuple[Dict[str, TerraformVariable], List[ModuleWarning], List[ModuleError]]:
        """
        Get all variables from the Terraform module.
        
        Returns:
            Tuple containing:
            - Dictionary of variables
            - List of warnings
            - List of errors
        """
        try:
            source_type, _ = self._get_source_type()
            variables = self._clone_repo() if source_type == 'git' else self.parse_directory(self.source_url)
            return variables, self.warnings, self.errors
        except Exception as e:
            self.add_error("Failed to get variables", str(e))
            return {}, self.warnings, self.errors 