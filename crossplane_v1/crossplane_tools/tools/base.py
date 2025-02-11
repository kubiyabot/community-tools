from typing import List, Optional, Dict, Any
from kubiya_sdk.tools import Tool, Arg
from pydantic import BaseModel

CROSSPLANE_ICON_URL = "https://59vlt2wq1mmini0e.public.blob.vercel-storage.com/crossplane-icon-color-05yZ9IQTXjBxS0XxV0pzG7lJhY6boJ.png"

# Define Secret class since it's not available in kubiya_sdk.tools
class Secret(BaseModel):
    name: str
    required: bool = True
    description: Optional[str] = None

# Default configuration values
DEFAULT_CONFIG = {
    "providers": {
        "aws": {
            "enabled": True,
            "sync_all": True,
            "include": [],
            "exclude": [],
            "secrets": [
                {"name": "AWS_ACCESS_KEY_ID", "required": True},
                {"name": "AWS_SECRET_ACCESS_KEY", "required": True},
                {"name": "AWS_SESSION_TOKEN", "required": False}
            ]
        },
        "gcp": {
            "enabled": True,
            "sync_all": True,
            "include": [],
            "exclude": [],
            "secrets": [
                {"name": "GOOGLE_CREDENTIALS", "required": True},
                {"name": "GOOGLE_PROJECT_ID", "required": True}
            ]
        }
    }
}

def get_provider_config(provider_name: str) -> Dict[str, Any]:
    """Get provider configuration from dynamic config."""
    EXAMPLE_CONFIG = """{
        "crossplane": {
            "providers": {
                "aws": {
                    "enabled": true,
                    "sync_all": true,
                    "include": ["s3", "eks"],
                    "exclude": ["rds"],
                    "secrets": [
                        {"name": "AWS_ACCESS_KEY_ID", "required": true},
                        {"name": "AWS_SECRET_ACCESS_KEY", "required": true},
                        {"name": "AWS_SESSION_TOKEN", "required": false}
                    ]
                },
                "gcp": {
                    "enabled": true,
                    "sync_all": true,
                    "include": ["gke", "storage"],
                    "exclude": ["sql"],
                    "secrets": [
                        {"name": "GOOGLE_CREDENTIALS", "required": true},
                        {"name": "GOOGLE_PROJECT_ID", "required": true}
                    ]
                }
            }
        }
    }"""

    try:
        from kubiya_sdk.tools.registry import tool_registry
        config = tool_registry.dynamic_config
    except Exception as e:
        raise ValueError(
            f"Failed to get dynamic configuration: {str(e)}\nExpected configuration structure:\n" + EXAMPLE_CONFIG
        )

    if not config:
        print("No dynamic configuration found, using defaults")
        return DEFAULT_CONFIG["providers"].get(provider_name, {})

    # Get Crossplane configuration
    crossplane_config = config.get('crossplane', {})
    if not crossplane_config:
        print("No Crossplane configuration found in dynamic config, using defaults")
        return DEFAULT_CONFIG["providers"].get(provider_name, {})

    # Get provider configuration
    provider_config = crossplane_config.get('providers', {}).get(provider_name, {})
    if not provider_config:
        print(f"No configuration found for provider {provider_name}, using defaults")
        return DEFAULT_CONFIG["providers"].get(provider_name, {})

    # Merge with defaults
    default_provider = DEFAULT_CONFIG["providers"].get(provider_name, {})
    merged_config = {
        "enabled": provider_config.get('enabled', default_provider.get('enabled', True)),
        "sync_all": provider_config.get('sync_all', default_provider.get('sync_all', True)),
        "include": provider_config.get('include', default_provider.get('include', [])),
        "exclude": provider_config.get('exclude', default_provider.get('exclude', [])),
        "secrets": provider_config.get('secrets', default_provider.get('secrets', []))
    }

    return merged_config

DEFAULT_MERMAID = """
```mermaid
classDiagram
    class Tool {
        <<interface>>
        +get_args()
        +get_content()
        +get_image()
    }
    class CrossplaneTool {
        -content: str
        -args: List[Arg]
        -image: str
        -secrets: List[Secret]
        +__init__(name, description, content, args, image, secrets)
        +_add_cluster_context(content)
        +get_args()
        +get_content()
        +get_image()
        +get_file_specs()
        +validate_args(args)
        +get_error_message(args)
        +get_environment()
        +get_secrets()
    }
    Tool <|-- CrossplaneTool
```
"""

class CrossplaneTool(Tool):
    """Base class for all Crossplane tools."""
    
    def __init__(self, name: str, description: str, args: Optional[List[Arg]] = None):
        super().__init__(
            name=name,
            description=description,
            args=args or [],
            icon_url=CROSSPLANE_ICON_URL
        )
    
    def get_provider_config(self, provider_name: str) -> Dict[str, Any]:
        """Get provider configuration from dynamic config."""
        try:
            from kubiya_sdk.tools.registry import tool_registry
            config = tool_registry.dynamic_config.get("crossplane", {}).get("providers", {}).get(provider_name, {})
            return {**DEFAULT_CONFIG.get(provider_name, {}), **config}
        except Exception as e:
            return DEFAULT_CONFIG.get(provider_name, {})

    def _add_cluster_context(self, content: str) -> str:
        """Add cluster context to the tool content."""
        return content

    async def execute(self, args: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute the tool with the given arguments."""
        try:
            # Implement the base execution logic here
            # This should be overridden by child classes
            raise NotImplementedError("Tool execution not implemented")
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }

    def get_args(self) -> List[Arg]:
        """Return the tool's arguments."""
        return self.args

    def get_content(self) -> str:
        """Return the tool's shell script content."""
        return self.content

    def get_image(self) -> str:
        """Return the Docker image to use."""
        return self.image

    def get_secrets(self) -> List[Secret]:
        """Return the tool's secrets."""
        return self.secrets

    def get_file_specs(self) -> List[FileSpec]:
        """Return the required file specifications."""
        return [
            FileSpec(
                destination="/root/.kube/config",
                description="Kubernetes configuration directory",
                source="$HOME/.kube/config"
            ),
            FileSpec(
                destination="/var/run/secrets/kubernetes.io/serviceaccount/token",
                description="Kubernetes service account tokens",
                source="/var/run/secrets/kubernetes.io/serviceaccount/token"
            ),
            FileSpec(
                destination="/workspace",
                description="Workspace directory for temporary files",
                source="$HOME/workspace"
            )
        ]

    def validate_args(self, args: Dict[str, Any]) -> bool:
        """Validate the provided arguments."""
        required_args = [arg.name for arg in self.args if arg.required]
        return all(arg in args and args[arg] for arg in required_args)

    def get_error_message(self, args: Dict[str, Any]) -> Optional[str]:
        """Return error message if arguments are invalid."""
        missing_args = []
        for arg in self.args:
            if arg.required and (arg.name not in args or not args[arg.name]):
                missing_args.append(arg.name)
        
        if missing_args:
            return f"Missing required arguments: {', '.join(missing_args)}"
        return None

    def get_environment(self) -> Dict[str, str]:
        """Return required environment variables."""
        return {
            "KUBECONFIG": "/root/.kube/config",
            "KUBERNETES_SERVICE_HOST": "kubernetes.default.svc",
            "KUBERNETES_SERVICE_PORT": "443"
        } 