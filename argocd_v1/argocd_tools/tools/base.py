from typing import List, Optional, Dict, Any
from kubiya_sdk.tools import Tool, Arg, FileSpec
from pydantic import BaseModel

ARGOCD_ICON_URL = "https://argo-cd.readthedocs.io/en/stable/assets/logo.png"

DEFAULT_MERMAID = """
```mermaid
classDiagram
    class Tool {
        <<interface>>
        +get_args()
        +get_content()
        +get_image()
    }
    class ArgoCDGitTool {
        -content: str
        -args: List[Arg]
        -image: str
        +__init__(name, description, content, args, image)
        +get_args()
        +get_content()
        +get_image()
        +get_file_specs()
        +validate_args(args)
        +get_error_message(args)
        +get_environment()
    }
    Tool <|-- ArgoCDGitTool
```
"""

class ArgoCDKubeTool(Tool):
    """Base class for ArgoCD tools that need kubectl access."""
    
    name: str
    description: str
    content: str = ""
    args: List[Arg] = []
    image: str = "alpine:3.18"
    icon_url: str = ARGOCD_ICON_URL
    type: str = "docker"
    
    def __init__(self, name, description, content, args=None, image="alpine:3.18"):
        # Enhanced setup script with kubectl and ArgoCD support
        setup_script = """
# Install required packages
echo "Installing required packages..." && \
apk update && \
apk add --no-cache curl jq git bash

# Install ArgoCD CLI with error handling
echo "Installing ArgoCD CLI..." && \
DOWNLOAD_URL=$(curl -s https://api.github.com/repos/argoproj/argo-cd/releases/latest | jq -r '.assets[] | select(.name == "argocd-linux-amd64") | .browser_download_url') && \
if [ -z "$DOWNLOAD_URL" ]; then
    echo "Error: Failed to get ArgoCD download URL"
    exit 1
fi && \
curl -sSL -o /usr/local/bin/argocd "$DOWNLOAD_URL" || {
    echo "Error: Failed to download ArgoCD CLI"
    exit 1
} && \
chmod +x /usr/local/bin/argocd || {
    echo "Error: Failed to make ArgoCD CLI executable"
    exit 1
}

# Install kubectl
echo "Installing kubectl..." && \
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" && \
chmod +x kubectl && \
mv kubectl /usr/local/bin/ || {
    echo "Error: Failed to install kubectl"
    exit 1
}

# Verify environment variables
if [ -z "$ARGOCD_SERVER" ]; then
    echo "Error: ARGOCD_SERVER environment variable is not set"
    exit 1
fi

if [ -z "$ARGOCD_AUTH_TOKEN" ]; then
    echo "Error: ARGOCD_AUTH_TOKEN environment variable is not set"
    exit 1
fi

# Set up kubectl configuration using service account
TOKEN_LOCATION="/tmp/kubernetes_context_token"
CERT_LOCATION="/tmp/kubernetes_context_cert"

if [ ! -f $TOKEN_LOCATION ] || [ ! -f $CERT_LOCATION ]; then
    echo "Error: Kubernetes context token or cert file not found"
    exit 1
fi

echo "Configuring kubectl..." && \
KUBE_TOKEN=$(cat $TOKEN_LOCATION)
kubectl config set-cluster in-cluster --server=https://kubernetes.default.svc \
                                    --certificate-authority=$CERT_LOCATION > /dev/null 2>&1 || {
    echo "Error: Failed to set kubectl cluster configuration"
    exit 1
}
kubectl config set-credentials in-cluster --token=$KUBE_TOKEN > /dev/null 2>&1 || {
    echo "Error: Failed to set kubectl credentials"
    exit 1
}
kubectl config set-context in-cluster --cluster=in-cluster --user=in-cluster > /dev/null 2>&1 || {
    echo "Error: Failed to set kubectl context"
    exit 1
}
kubectl config use-context in-cluster > /dev/null 2>&1 || {
    echo "Error: Failed to switch kubectl context"
    exit 1
}

# Test connections
echo "Testing ArgoCD connection..." && \
if ! argocd version --server "$ARGOCD_SERVER" --auth-token "$ARGOCD_AUTH_TOKEN" --insecure; then
    echo "Error: Failed to verify ArgoCD CLI installation and authentication"
    exit 1
fi

echo "Testing kubectl connection..." && \
if ! kubectl version --client; then
    echo "Error: Failed to verify kubectl installation"
    exit 1
fi

"""
        enhanced_content = setup_script + "\n" + content
        
        # Add auth flags to all argocd commands in the content
        enhanced_content = enhanced_content.replace("argocd ", 'argocd --server "$ARGOCD_SERVER" --auth-token "$ARGOCD_AUTH_TOKEN" --insecure ')
        
        file_specs = [
            FileSpec(
                source="/var/run/secrets/kubernetes.io/serviceaccount/token",
                destination="/tmp/kubernetes_context_token"
            ),
            FileSpec(
                source="/var/run/secrets/kubernetes.io/serviceaccount/ca.crt",
                destination="/tmp/kubernetes_context_cert"
            )
        ]

        super().__init__(
            name=name,
            description=description,
            content=enhanced_content,
            args=args or [],
            image=image,
            icon_url=ARGOCD_ICON_URL,
            type="docker",
            secrets=["ARGOCD_AUTH_TOKEN"],
            env=["ARGOCD_SERVER"],
            with_files=file_specs
        )

class ArgoCDGitTool(Tool):
    """Base class for ArgoCD tools that interact with Git repositories."""
    
    name: str
    description: str
    content: str = ""
    args: List[Arg] = []
    image: str = "alpine:3.18"
    icon_url: str = ARGOCD_ICON_URL
    type: str = "docker"
    mermaid: str = DEFAULT_MERMAID
    
    def __init__(self, name, description, content, args=None, image="alpine:3.18"):
        # Enhanced setup script with Git and ArgoCD support
        setup_script = """
# Install required packages
echo "Installing required packages..." && \
apk update && \
apk add --no-cache curl jq git bash

# Install ArgoCD CLI with error handling
echo "Installing ArgoCD CLI..." && \
DOWNLOAD_URL=$(curl -s https://api.github.com/repos/argoproj/argo-cd/releases/latest | jq -r '.assets[] | select(.name == "argocd-linux-amd64") | .browser_download_url') && \
if [ -z "$DOWNLOAD_URL" ]; then
    echo "Error: Failed to get ArgoCD download URL"
    exit 1
fi && \
curl -sSL -o /usr/local/bin/argocd "$DOWNLOAD_URL" || {
    echo "Error: Failed to download ArgoCD CLI"
    exit 1
} && \
chmod +x /usr/local/bin/argocd || {
    echo "Error: Failed to make ArgoCD CLI executable"
    exit 1
}

# Verify environment variables
if [ -z "$ARGOCD_SERVER" ]; then
    echo "Error: ARGOCD_SERVER environment variable is not set"
    exit 1
fi

if [ -z "$ARGOCD_AUTH_TOKEN" ]; then
    echo "Error: ARGOCD_AUTH_TOKEN environment variable is not set"
    exit 1
fi

if [ -z "$GH_TOKEN" ]; then
    echo "Error: GH_TOKEN environment variable is not set"
    exit 1
fi

# Configure Git
echo "Configuring Git credentials..." && \
git config --global credential.helper store
echo "https://oauth2:${GH_TOKEN}@github.com" > ~/.git-credentials
git config --global user.name "Kubiya Bot"
git config --global user.email "bot@kubiya.ai"

# Test ArgoCD connection
echo "Testing ArgoCD connection..." && \
if ! argocd version --server "$ARGOCD_SERVER" --auth-token "$ARGOCD_AUTH_TOKEN" --insecure; then
    echo "Error: Failed to verify ArgoCD CLI installation and authentication"
    exit 1
fi

# Create workspace for Git operations
echo "Creating Git workspace..." && \
WORKSPACE="/tmp/argocd_workspace"
mkdir -p "$WORKSPACE"
cd "$WORKSPACE"

"""
        enhanced_content = setup_script + "\n" + content + "\n\n# Cleanup\ncd /\nrm -rf \"$WORKSPACE\""
        
        # Add auth flags to all argocd commands in the content
        enhanced_content = enhanced_content.replace("argocd ", 'argocd --server "$ARGOCD_SERVER" --auth-token "$ARGOCD_AUTH_TOKEN" --insecure ')
        
        super().__init__(
            name=name,
            description=description,
            content=enhanced_content,
            args=args or [],
            image=image,
            icon_url=ARGOCD_ICON_URL,
            type="docker",
            secrets=["ARGOCD_AUTH_TOKEN", "GH_TOKEN"],
            env=["ARGOCD_SERVER"]
        )

    def get_args(self) -> List[Arg]:
        """Return the tool's arguments."""
        return self.args

    def get_content(self) -> str:
        """Return the tool's shell script content."""
        return self.content

    def get_image(self) -> str:
        """Return the Docker image to use."""
        return self.image

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

# Keep the original ArgoCDTool for simpler operations
class ArgoCDTool(Tool):
    """Base class for simple ArgoCD tools that don't need Git integration."""
    
    name: str
    description: str
    content: str = ""
    args: List[Arg] = []
    image: str = "alpine:3.18"
    icon_url: str = ARGOCD_ICON_URL
    type: str = "docker"
    mermaid: str = DEFAULT_MERMAID
    
    def __init__(self, name, description, content, args=None, image="alpine:3.18"):
        # Improved installation and authentication script
        setup_script = """
# Install required packages
apk add --no-cache curl jq && \
echo "Installing required packages..." && \
apk update && \
apk add --no-cache curl jq bash

# Install ArgoCD CLI with error handling
echo "Installing ArgoCD CLI..." && \
DOWNLOAD_URL=$(curl -s https://api.github.com/repos/argoproj/argo-cd/releases/latest | jq -r '.assets[] | select(.name == "argocd-linux-amd64") | .browser_download_url') && \
if [ -z "$DOWNLOAD_URL" ]; then
    echo "Error: Failed to get ArgoCD download URL"
    exit 1
fi && \
curl -sSL -o /usr/local/bin/argocd "$DOWNLOAD_URL" || {
    echo "Error: Failed to download ArgoCD CLI"
    exit 1
} && \
chmod +x /usr/local/bin/argocd || {
    echo "Error: Failed to make ArgoCD CLI executable"
    exit 1
}

# Verify environment variables
if [ -z "$ARGOCD_SERVER" ]; then
    echo "Error: ARGOCD_SERVER environment variable is not set"
    exit 1
fi

if [ -z "$ARGOCD_AUTH_TOKEN" ]; then
    echo "Error: ARGOCD_AUTH_TOKEN environment variable is not set"
    exit 1
fi

# Test connection with proper error handling
echo "Testing ArgoCD connection..." && \
if ! argocd version --server "$ARGOCD_SERVER" --auth-token "$ARGOCD_AUTH_TOKEN" --insecure; then
    echo "Error: Failed to verify ArgoCD CLI installation and authentication"
    exit 1
fi

"""
        enhanced_content = setup_script + "\n" + content
        
        # Add auth flags to all argocd commands in the content
        enhanced_content = enhanced_content.replace("argocd ", 'argocd --server "$ARGOCD_SERVER" --auth-token "$ARGOCD_AUTH_TOKEN" --insecure ')
        
        super().__init__(
            name=name,
            description=description,
            content=enhanced_content,
            args=args or [],
            image=image,
            icon_url=ARGOCD_ICON_URL,
            type="docker",
            secrets=["ARGOCD_AUTH_TOKEN"],
            env=["ARGOCD_SERVER"]
        )

    def get_args(self) -> List[Arg]:
        """Return the tool's arguments."""
        return self.args

    def get_content(self) -> str:
        """Return the tool's shell script content."""
        return self.content

    def get_image(self) -> str:
        """Return the Docker image to use."""
        return self.image

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