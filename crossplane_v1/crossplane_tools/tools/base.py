from typing import List, Optional, Dict, Any
from kubiya_sdk.tools import Tool, Arg
from pydantic import BaseModel

CROSSPLANE_ICON_URL = "https://59vlt2wq1mmini0e.public.blob.vercel-storage.com/crossplane-icon-color-05yZ9IQTXjBxS0XxV0pzG7lJhY6boJ.png"

# Define base models
class Secret(BaseModel):
    name: str
    required: bool = True
    description: Optional[str] = None

class FileSpec(BaseModel):
    destination: str
    source: str
    description: Optional[str] = None

# Default provider configuration
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
    try:
        from kubiya_sdk.tools.registry import tool_registry
        config = tool_registry.dynamic_config
        if not config:
            return DEFAULT_CONFIG["providers"].get(provider_name, {})

        crossplane_config = config.get('crossplane', {})
        if not crossplane_config:
            return DEFAULT_CONFIG["providers"].get(provider_name, {})

        provider_config = crossplane_config.get('providers', {}).get(provider_name, {})
        if not provider_config:
            return DEFAULT_CONFIG["providers"].get(provider_name, {})

        # Merge with defaults
        default_provider = DEFAULT_CONFIG["providers"].get(provider_name, {})
        return {
            "enabled": provider_config.get('enabled', default_provider.get('enabled', True)),
            "sync_all": provider_config.get('sync_all', default_provider.get('sync_all', True)),
            "include": provider_config.get('include', default_provider.get('include', [])),
            "exclude": provider_config.get('exclude', default_provider.get('exclude', [])),
            "secrets": provider_config.get('secrets', default_provider.get('secrets', []))
        }
    except Exception as e:
        return DEFAULT_CONFIG["providers"].get(provider_name, {})

class CrossplaneToolConfig(BaseModel):
    name: str
    description: str
    content: Optional[str] = ""
    args: List[Arg] = []
    image: str = "crossplane/crossplane:v1.14.0"
    icon_url: str = CROSSPLANE_ICON_URL
    type: str = "docker"
    secrets: List[Secret] = []
    file_specs: List[FileSpec] = []
    env_vars: Dict[str, str] = {}

class CrossplaneTool(Tool):
    """Base class for all Crossplane tools."""
    
    def __init__(
        self,
        name: str,
        description: str,
        content: Optional[str] = "",
        args: Optional[List[Arg]] = None,
        image: str = "crossplane/crossplane:v1.14.0",
        secrets: Optional[List[Secret]] = None,
        file_specs: Optional[List[FileSpec]] = None,
        env_vars: Optional[Dict[str, str]] = None
    ):
        self.config = CrossplaneToolConfig(
            name=name,
            description=description,
            content=content,
            args=args or [],
            image=image,
            secrets=secrets or [],
            file_specs=file_specs or self._default_file_specs(),
            env_vars=env_vars or self._default_env_vars()
        )
        
        super().__init__(
            name=name,
            description=description,
            args=args or [],
            icon_url=CROSSPLANE_ICON_URL
        )

    def _default_file_specs(self) -> List[FileSpec]:
        """Return default file specifications."""
        return [
            FileSpec(
                destination="/root/.kube/config",
                source="$HOME/.kube/config",
                description="Kubernetes configuration directory"
            ),
            FileSpec(
                destination="/var/run/secrets/kubernetes.io/serviceaccount/token",
                source="/var/run/secrets/kubernetes.io/serviceaccount/token",
                description="Kubernetes service account tokens"
            ),
            FileSpec(
                destination="/workspace",
                source="$HOME/workspace",
                description="Workspace directory for temporary files"
            )
        ]

    def _default_env_vars(self) -> Dict[str, str]:
        """Return default environment variables."""
        return {
            "KUBECONFIG": "/root/.kube/config",
            "KUBERNETES_SERVICE_HOST": "kubernetes.default.svc",
            "KUBERNETES_SERVICE_PORT": "443"
        }

    async def execute(self, args: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute the tool with the given arguments."""
        try:
            if not self.validate_args(args or {}):
                error_msg = self.get_error_message(args or {})
                return {"status": "error", "message": error_msg}
            
            # Tool-specific execution logic should be implemented by subclasses
            raise NotImplementedError("Tool execution not implemented")
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def validate_args(self, args: Dict[str, Any]) -> bool:
        """Validate the provided arguments."""
        if not args:
            return not any(arg.required for arg in self.config.args)
        return all(arg.name in args for arg in self.config.args if arg.required)

    def get_error_message(self, args: Dict[str, Any]) -> str:
        """Return error message if arguments are invalid."""
        missing = [arg.name for arg in self.config.args if arg.required and arg.name not in args]
        if missing:
            return f"Missing required arguments: {', '.join(missing)}"
        return "Invalid arguments provided"

    def get_content(self) -> str:
        """Return the tool's content."""
        return self.config.content

    def get_image(self) -> str:
        """Return the tool's Docker image."""
        return self.config.image

    def get_secrets(self) -> List[Secret]:
        """Return the tool's secrets."""
        return self.config.secrets

    def get_file_specs(self) -> List[FileSpec]:
        """Return the tool's file specifications."""
        return self.config.file_specs

    def get_env_vars(self) -> Dict[str, str]:
        """Return the tool's environment variables."""
        return self.config.env_vars

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

    def get_environment(self) -> Dict[str, str]:
        """Return required environment variables."""
        return {
            "KUBECONFIG": "/root/.kube/config",
            "KUBERNETES_SERVICE_HOST": "kubernetes.default.svc",
            "KUBERNETES_SERVICE_PORT": "443"
        } 