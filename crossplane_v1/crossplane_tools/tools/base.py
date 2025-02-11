from typing import List, Optional, Dict, Any
from kubiya_sdk.tools import Tool, Arg, FileSpec
from pydantic import BaseModel

CROSSPLANE_ICON_URL = "https://59vlt2wq1mmini0e.public.blob.vercel-storage.com/crossplane-icon-color-05yZ9IQTXjBxS0XxV0pzG7lJhY6boJ.png"

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
        +__init__(name, description, content, args, image)
        +_add_cluster_context(content)
        +get_args()
        +get_content()
        +get_image()
        +get_file_specs()
        +validate_args(args)
        +get_error_message(args)
        +get_environment()
    }
    Tool <|-- CrossplaneTool
```
"""

class CrossplaneTool(Tool):
    """Base class for all Crossplane tools."""

    def __init__(self, name: str, description: str, content: str = "", args: List[Arg] = None, image: str = None, **kwargs):
        """Initialize the Crossplane tool."""
        # Process content if provided
        if content:
            content = self._add_cluster_context(content)
        
        # Create the model data
        model_data = {
            "name": name,
            "description": description,
            "content": content,
            "args": args or [],
            "icon_url": CROSSPLANE_ICON_URL,
            "type": "docker",
            "image": image or "crossplane/crossplane:v1.14.0",
            "mermaid": DEFAULT_MERMAID,
            "with_files": [
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
            "env": [
                "KUBECONFIG",
                "KUBERNETES_SERVICE_HOST",
                "KUBERNETES_SERVICE_PORT"
            ]
        }
        
        # Update with any additional kwargs
        model_data.update(kwargs)
        
        # Initialize the parent class with the model data
        super().__init__(**model_data)

    def _add_cluster_context(self, content: str) -> str:
        """Add cluster context setup and dependency installation to the shell script content."""
        setup = """
# Install required dependencies
install_dependencies() {
    echo "Installing required dependencies..."
    
    # Install kubectl if not present
    if ! command -v kubectl &> /dev/null; then
        echo "Installing kubectl..."
        curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
        chmod +x kubectl
        mv kubectl /usr/local/bin/
    fi

    # Install helm if not present
    if ! command -v helm &> /dev/null; then
        echo "Installing helm..."
        curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3
        chmod 700 get_helm.sh
        ./get_helm.sh
        rm get_helm.sh
    fi

    # Install yq if not present
    if ! command -v yq &> /dev/null; then
        echo "Installing yq..."
        wget -qO /usr/local/bin/yq https://github.com/mikefarah/yq/releases/latest/download/yq_linux_amd64
        chmod +x /usr/local/bin/yq
    fi

    # Install jq if not present
    if ! command -v jq &> /dev/null; then
        echo "Installing jq..."
        apt-get update && apt-get install -y jq
    fi
}

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

# Install dependencies
install_dependencies

# Set up Kubernetes configuration for in-cluster access
if [ -f /var/run/secrets/kubernetes.io/serviceaccount/token ]; then
    echo "Running in-cluster, setting up Kubernetes configuration..."
    APISERVER=https://kubernetes.default.svc
    SERVICEACCOUNT=/var/run/secrets/kubernetes.io/serviceaccount
    TOKEN=$(cat ${SERVICEACCOUNT}/token)
    CACERT=${SERVICEACCOUNT}/ca.crt

    # Set up kubeconfig
    kubectl config set-cluster in-cluster --server=${APISERVER} --certificate-authority=${CACERT}
    kubectl config set-credentials sa --token=${TOKEN}
    kubectl config set-context in-cluster --cluster=in-cluster --user=sa
    kubectl config use-context in-cluster
fi

# Validate cluster access
validate_cluster_access

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

"""
        return setup + content

    def get_args(self) -> List[Arg]:
        """Return the tool's arguments."""
        return self.args

    def get_content(self) -> str:
        """Return the tool's shell script content."""
        return self.content

    def get_image(self) -> str:
        """Return the Docker image to use."""
        return self.image

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