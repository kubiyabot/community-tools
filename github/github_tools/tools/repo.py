from kubiya_workflow_sdk.tools import Arg
from .base import GitHubCliTool
from kubiya_workflow_sdk.tools.registry import tool_registry

# Core repository operations
repo_create = GitHubCliTool(
    name="github_repo_create",
    description="Create a new GitHub repository",
    content="""
    echo "🚀 Creating new GitHub repository..."
    echo "📝 Name: ${name}"
    [[ -n "${org}" ]] && echo "🏢 Organization: ${org}"
    [[ "${private}" == "true" ]] && echo "🔒 Visibility: Private" || echo "🌎 Visibility: Public"

    REPO_NAME="$([[ -n "${org}" ]] && echo "${org}/${name}" || echo "${name}")"

    if ! gh repo create "${REPO_NAME}" \
        $([ "${private}" == "true" ] && echo "--private" || echo "--public") \
        $([ -n "${description}" ] && echo "--description \"${description}\"") \
        $([ -n "${homepage}" ] && echo "--homepage ${homepage}") \
        $([ "${has_issues}" == "false" ] && echo "--disable-issues") \
        $([ "${has_wiki}" == "false" ] && echo "--disable-wiki"); then
        echo "❌ Failed to create repository"
        exit 1
    fi

    echo "✨ Repository created successfully!"
    echo "🔗 Repository URL: https://github.com/${REPO_NAME}"
    """,
    args=[
        Arg(name="name", type="str", description="Repository name", required=True),
        Arg(name="org", type="str", description="Organization name", required=False),
        Arg(name="private", type="bool", description="Create private repository", required=False),
        Arg(name="description", type="str", description="Repository description", required=False),
        Arg(name="homepage", type="str", description="Repository homepage URL", required=False),
        Arg(name="has_issues", type="bool", description="Enable issues", required=False, default=True),
        Arg(name="has_wiki", type="bool", description="Enable wiki", required=False, default=True),
    ],
)

# Add other repository-specific tools...