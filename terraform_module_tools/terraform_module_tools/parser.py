import os
import json
import tempfile
import subprocess
import requests
from typing import Dict, Any, List, Optional, Tuple
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
    def __init__(
        self,
        source_url: str,
        ref: Optional[str] = None,
        subfolder: Optional[str] = None
    ):
        self.source_url = source_url
        self.ref = ref
        self.subfolder = subfolder
        self.warnings = []
        self.errors = []

    def _handle_registry_module(self, source: str) -> str:
        """Handle Terraform registry module source."""
        # Parse registry source (format: namespace/name/provider)
        parts = source.split('/')
        if len(parts) != 3:
            raise ValueError(f"Invalid registry source format: {source}")
        
        namespace, name, provider = parts
        
        # For well-known modules, we can use their GitHub URLs directly
        if namespace == "terraform-aws-modules":
            # Convert to GitHub URL
            github_url = f"https://github.com/terraform-aws-modules/terraform-{provider}-{name}"
            if self.ref:
                github_url += f"/tree/{self.ref}"
            return github_url
        
        # For other modules, try the registry API
        try:
            # Construct registry API URL
            registry_url = f"https://registry.terraform.io/v1/modules/{namespace}/{name}/{provider}"
            
            # Get module info from registry
            response = requests.get(registry_url)
            response.raise_for_status()
            module_info = response.json()
            
            # Get the source URL from the latest version or specified version
            version = self.ref or module_info.get('version')
            if not version:
                raise ValueError(f"No version specified for module {source}")
            
            # Get source URL
            source_url = module_info.get('source') or f"https://github.com/{namespace}/terraform-{provider}-{name}"
            
            # Add version if specified
            if version and not source_url.endswith(version):
                if source_url.startswith('http'):
                    source_url += f"/tree/{version}"
                else:
                    source_url += f"?ref={version}"
            
            return source_url
            
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Failed to fetch module from registry: {str(e)}")

    def get_variables(self) -> Tuple[Dict[str, Any], List[str], List[str]]:
        """Get variables from the Terraform module."""
        try:
            # Handle different source types
            if '/' in self.source_url and not self.source_url.startswith(('http://', 'https://', 'git@', '/')):
                # This is a registry module
                source_url = self._handle_registry_module(self.source_url)
            else:
                source_url = self.source_url

            # Create temporary directory
            with tempfile.TemporaryDirectory() as temp_dir:
                # Clone repository
                if source_url.startswith(('http://', 'https://', 'git@')):
                    # Git repository
                    try:
                        subprocess.run(['git', 'clone', source_url, temp_dir], check=True, capture_output=True, text=True)
                        if self.ref:
                            subprocess.run(['git', 'checkout', self.ref], cwd=temp_dir, check=True, capture_output=True, text=True)
                    except subprocess.CalledProcessError as e:
                        raise ValueError(f"Git operation failed: {e.stderr}")
                else:
                    # Local path
                    if not os.path.exists(source_url):
                        raise ValueError(f"Local path not found: {source_url}")
                    os.system(f"cp -r {source_url}/* {temp_dir}/")

                # Change to module directory if subfolder specified
                module_dir = os.path.join(temp_dir, self.subfolder) if self.subfolder else temp_dir

                # Find all .tf files
                variables = {}
                for root, _, files in os.walk(module_dir):
                    for file in files:
                        if file.endswith('.tf'):
                            file_path = os.path.join(root, file)
                            try:
                                # Use hcl2json to parse the file
                                result = subprocess.run(
                                    ['hcl2json', file_path],
                                    capture_output=True,
                                    text=True,
                                    check=True
                                )
                                tf_json = json.loads(result.stdout)
                                
                                # Extract variables
                                if 'variable' in tf_json:
                                    for var_name, var_config in tf_json['variable'].items():
                                        variables[var_name] = {
                                            'type': var_config.get('type', 'string'),
                                            'description': var_config.get('description', ''),
                                            'default': var_config.get('default'),
                                            'required': 'default' not in var_config
                                        }
                            except subprocess.CalledProcessError as e:
                                self.warnings.append(f"Failed to parse {file_path}: {e.stderr}")
                            except json.JSONDecodeError as e:
                                self.warnings.append(f"Invalid JSON from {file_path}: {str(e)}")
                            except Exception as e:
                                self.warnings.append(f"Error processing {file_path}: {str(e)}")

                return variables, self.warnings, self.errors

        except Exception as e:
            self.errors.append(f"❌ {self.source_url}: Failed to get variables\nDetails: {str(e)}")
            return {}, self.warnings, self.errors