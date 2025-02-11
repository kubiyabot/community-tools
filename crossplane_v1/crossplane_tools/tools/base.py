from typing import List, Optional, Dict, Any
from kubiya_sdk.tools import Tool, Arg, FileSpec

CROSSPLANE_ICON_URL = "https://59vlt2wq1mmini0e.public.blob.vercel-storage.com/crossplane-icon-color-05yZ9IQTXjBxS0XxV0pzG7lJhY6boJ.png"

class CrossplaneTool(Tool):
    """Base class for all Crossplane tools."""

    def __init__(self, name: str, description: str, content: str, args: List[Arg], image: str = "crossplane/crossplane:v1.14.0", mermaid: str = None):
        super().__init__(
            name=name,
            description=description,
            icon_url=CROSSPLANE_ICON_URL,
            mermaid=mermaid or """
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
        )
        self.content = self._add_cluster_context(content)
        self.args = args
        self.image = image

    def _add_cluster_context(self, content: str) -> str:
        """Add cluster context setup to the shell script content."""
        context_setup = """
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

# Function to handle errors
handle_error() {
    echo "Error: $1"
    exit 1
}

# Set error handling
set -e
trap 'handle_error "Command failed: $BASH_COMMAND"' ERR

"""
        return context_setup + content

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
                mount_path="/root/.kube",
                description="Kubernetes configuration directory"
            ),
            FileSpec(
                mount_path="/var/run/secrets/kubernetes.io/serviceaccount",
                description="Kubernetes service account tokens"
            ),
            FileSpec(
                mount_path="/workspace",
                description="Workspace directory for temporary files"
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