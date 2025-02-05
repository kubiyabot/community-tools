# k8s_tools/tools/base.py
from kubiya_sdk.tools import Tool, Arg, FileSpec
import os

KUBERNETES_ICON_URL = "https://kubernetes.io/icons/icon-128x128.png"

# Default truncation settings
MAX_ITEMS = 50  # Maximum number of items to show in lists
MAX_OUTPUT_WIDTH = 120  # Maximum width for output lines
MAX_EVENTS = 25  # Maximum number of events to show
MAX_LOGS = 1000  # Maximum number of log lines

def read_file_content(path):
    """Helper function to read file content"""
    try:
        with open(path, 'r') as f:
            return f.read()
    except Exception as e:
        print(f"Warning: Could not read file {path}: {e}")
        return None

class KubernetesTool(Tool):
    def __init__(self, name, description, content, args, image="bitnami/kubectl:latest"):
        # Get the directory of the current file
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        templates_dir = os.path.join(current_dir, 'templates')

        # Define file specs for all required files
        file_specs = [
            # Kubernetes auth files
            FileSpec(
                source="/var/run/secrets/kubernetes.io/serviceaccount/token",
                destination="/tmp/kubernetes_context_token"
            ),
            FileSpec(
                source="/var/run/secrets/kubernetes.io/serviceaccount/ca.crt",
                destination="/tmp/kubernetes_context_cert"
            ),
            # Helper shell scripts with direct content
            FileSpec(
                content=read_file_content(os.path.join(templates_dir, 'k8s_helpers.sh')),
                destination="/tmp/k8s_helpers.sh"
            ),
            FileSpec(
                content=read_file_content(os.path.join(templates_dir, 'k8s_context.sh')),
                destination="/tmp/k8s_context.sh"
            ),
            FileSpec(
                content=read_file_content(os.path.join(templates_dir, 'resource_finder.sh')),
                destination="/tmp/resource_finder.sh"
            )
        ]

        # Filter out any FileSpecs where content couldn't be read
        file_specs = [spec for spec in file_specs if not hasattr(spec, 'content') or spec.content is not None]

        # Combine scripts with proper line endings
        full_content = (
            "# Source helper scripts\n"
            "source /tmp/k8s_context.sh\n"
            "source /tmp/k8s_helpers.sh\n\n"
            "# Begin main script\n"
            f"{content}\n"
        )

        super().__init__(
            name=name,
            description=description,
            icon_url=KUBERNETES_ICON_URL,
            type="docker",
            image=image,
            content=full_content,
            args=args,
            with_files=file_specs,
        )

# Example usage:
kubectl_cli = KubernetesTool(
    name="kubectl_cli",
    description="Runs any Kubernetes commands using the `kubectl` binary.",
    content="kubectl {{.command}}",
    args=[
        Arg(
            name="command",
            description="The Kubernetes CLI command to run. Do not use `kubectl`, only enter its command.",
            required=True
        )
    ]
)
