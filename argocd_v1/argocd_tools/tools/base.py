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
apk add --no-cache curl jq git && \
VERSION=$(curl --silent "https://api.github.com/repos/argoproj/argo-cd/releases/latest" | jq -r .tag_name) && \
curl -sSL -o /usr/local/bin/argocd https://github.com/argoproj/argo-cd/releases/download/${VERSION}/argocd-linux-amd64 && \
chmod +x /usr/local/bin/argocd

# Verify environment variables
if [ -z "$ARGOCD_SERVER" ]; then
    echo "Error: ARGOCD_SERVER environment variable is not set"
    exit 1
fi

if [ -z "$ARGOCD_PASSWORD" ]; then
    echo "Error: ARGOCD_PASSWORD environment variable is not set"
    exit 1
fi

if [ -z "$GH_TOKEN" ]; then
    echo "Error: GH_TOKEN environment variable is not set"
    exit 1
fi

# Configure Git
git config --global credential.helper store
echo "https://oauth2:${GH_TOKEN}@github.com" > ~/.git-credentials
git config --global user.name "Kubiya Bot"
git config --global user.email "bot@kubiya.ai"

# Login to ArgoCD
if ! argocd login "$ARGOCD_SERVER" --username admin --password "$ARGOCD_PASSWORD" --insecure; then
    echo "Error: Failed to login to ArgoCD"
    exit 1
fi

# Test ArgoCD connection
if ! argocd version; then
    echo "Error: Failed to verify ArgoCD CLI installation"
    exit 1
fi

# Create workspace for Git operations
WORKSPACE="/tmp/argocd_workspace"
mkdir -p "$WORKSPACE"
cd "$WORKSPACE"

"""
        enhanced_content = setup_script + "\n" + content + "\n\n# Cleanup\ncd /\nrm -rf \"$WORKSPACE\""
        
        super().__init__(
            name=name,
            description=description,
            content=enhanced_content,
            args=args or [],
            image=image,
            icon_url=ARGOCD_ICON_URL,
            type="docker",
            secrets=["ARGOCD_PASSWORD", "GH_TOKEN"],
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
VERSION=$(curl --silent "https://api.github.com/repos/argoproj/argo-cd/releases/latest" | jq -r .tag_name) && \
curl -sSL -o /usr/local/bin/argocd https://github.com/argoproj/argo-cd/releases/download/${VERSION}/argocd-linux-amd64 && \
chmod +x /usr/local/bin/argocd

# Verify environment variables
if [ -z "$ARGOCD_SERVER" ]; then
    echo "Error: ARGOCD_SERVER environment variable is not set"
    exit 1
fi

if [ -z "$ARGOCD_PASSWORD" ]; then
    echo "Error: ARGOCD_PASSWORD environment variable is not set"
    exit 1
fi

# Login to ArgoCD
if ! argocd login "$ARGOCD_SERVER" --username admin --password "$ARGOCD_PASSWORD" --insecure; then
    echo "Error: Failed to login to ArgoCD"
    exit 1
fi

# Test connection
if ! argocd version; then
    echo "Error: Failed to verify ArgoCD CLI installation"
    exit 1
fi

"""
        enhanced_content = setup_script + "\n" + content
        
        super().__init__(
            name=name,
            description=description,
            content=enhanced_content,
            args=args or [],
            image=image,
            icon_url=ARGOCD_ICON_URL,
            type="docker",
            secrets=["ARGOCD_PASSWORD"],
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