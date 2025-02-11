from typing import List, Optional, Dict, Any
from kubiya_sdk.tools import Tool, Arg, FileSpec, Secret
from pydantic import BaseModel

CROSSPLANE_ICON_URL = "https://59vlt2wq1mmini0e.public.blob.vercel-storage.com/crossplane-icon-color-05yZ9IQTXjBxS0XxV0pzG7lJhY6boJ.png"

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
    
    # Define model fields
    name: str
    description: str
    content: str = ""
    args: List[Arg] = []
    image: str = "crossplane/crossplane:v1.14.0"
    icon_url: str = CROSSPLANE_ICON_URL
    type: str = "docker"
    mermaid: str = DEFAULT_MERMAID
    secrets: List[Secret] = []
    with_files: List[Dict[str, str]] = [
        {
            "destination": "/root/.kube/config",
            "description": "Kubernetes configuration directory",
            "source": "$HOME/.kube/config"
        },
        {
            "destination": "/var/run/secrets/kubernetes.io/serviceaccount/token",
            "description": "Kubernetes service account tokens",
            "source": "/var/run/secrets/kubernetes.io/serviceaccount/token"
        },
        {
            "destination": "/workspace",
            "description": "Workspace directory for temporary files",
            "source": "$HOME/workspace"
        }
    ]
    env: List[str] = ["KUBECONFIG", "KUBERNETES_SERVICE_HOST", "KUBERNETES_SERVICE_PORT"]

    def __init__(self, name, description, content, args=None, image="crossplane/crossplane:v1.14.0", secrets=None):
        # Initialize the tool with the combined content
        super().__init__(
            name=name,
            description=description,
            content=self._add_cluster_context(content),
            args=args or [],
            image=image,
            icon_url=CROSSPLANE_ICON_URL,
            type="docker",
            secrets=secrets or [],
            with_files=[
                {
                    "destination": "/root/.kube/config",
                    "description": "Kubernetes configuration directory",
                    "source": "$HOME/.kube/config"
                },
                {
                    "destination": "/var/run/secrets/kubernetes.io/serviceaccount/token",
                    "description": "Kubernetes service account tokens",
                    "source": "/var/run/secrets/kubernetes.io/serviceaccount/token"
                },
                {
                    "destination": "/workspace",
                    "description": "Workspace directory for temporary files",
                    "source": "$HOME/workspace"
                }
            ],
            env=[
                "KUBECONFIG",
                "KUBERNETES_SERVICE_HOST",
                "KUBERNETES_SERVICE_PORT"
            ]
        )

    def _add_cluster_context(self, content: str) -> str:
        """Add cluster context setup and dependency installation to the shell script content."""
        setup = """
# Begin helper functions
{
    # Function to validate cluster access
    validate_cluster_access() {
        if ! kubectl cluster-info &> /dev/null; then
            echo "Error: Unable to access Kubernetes cluster"
            exit 1
        fi
    }

    # Function to handle errors
    handle_error() {
        local exit_code=$?
        local command=$BASH_COMMAND
        echo "Error: Command '$command' failed with exit code $exit_code"
        exit $exit_code
    }

    # Set error handling
    set -e
    trap 'handle_error' ERR

    # Common utility functions
    get_resource_name() {
        local yaml_content="$1"
        echo "$yaml_content" | yq e '.metadata.name' -
    }

    get_resource_namespace() {
        local yaml_content="$1"
        local namespace=$(echo "$yaml_content" | yq e '.metadata.namespace // "default"' -)
        echo "$namespace"
    }

    wait_for_resource() {
        local kind="$1"
        local name="$2"
        local namespace="$3"
        local timeout="${4:-300s}"
        
        echo "Waiting for $kind/$name in namespace $namespace to be ready..."
        kubectl wait --for=condition=ready "$kind/$name" -n "$namespace" --timeout="$timeout"
    }

    verify_crd_exists() {
        local crd="$1"
        if ! kubectl get crd "$crd" &> /dev/null; then
            echo "Error: CRD $crd not found"
            exit 1
        fi
    }

    # Function to discover provider resources
    discover_provider_resources() {
        local provider="$1"
        kubectl get crds -l crossplane.io/provider=$provider -o custom-columns=NAME:.metadata.name,GROUP:.spec.group,VERSION:.spec.versions[0].name,KIND:.spec.names.kind --no-headers
    }

    # Function to generate resource template
    generate_resource_template() {
        local crd="$1"
        local name="$2"
        kubectl get crd $crd -o jsonpath='{.spec.versions[0].schema.openAPIV3Schema}' | yq e -P -
    }
}
"""
        return setup + "\n" + content

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