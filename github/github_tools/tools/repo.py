from kubiya_sdk.tools import Arg
from .base import GitHubCliTool
from kubiya_sdk.tools.registry import tool_registry


repo_clone = GitHubCliTool(
    name="github_repo_clone",
    description="Clone a GitHub repository",
    content="""
    echo "📥 Cloning GitHub repository..."
    echo "📝 Repository: ${repository}"
    [[ -n "${directory}" ]] && echo "📁 Target directory: ${directory}"

    if ! gh repo clone "${repository}" ${directory:+"$directory"}; then
        echo "❌ Failed to clone repository"
        exit 1
    fi

    echo "✅ Repository cloned successfully!"
    """,
    args=[
        Arg(
            name="repository", 
            type="str", 
            description="Repository to clone (format: owner/repo)", 
            required=True
        ),
        Arg(
            name="directory", 
            type="str", 
            description="Directory to clone into", 
            required=False
        ),
    ],
)

# Register both tools
tool_registry.register(repo_clone)

# Add other repository-specific tools...