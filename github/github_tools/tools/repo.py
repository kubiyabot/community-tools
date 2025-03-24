from kubiya_sdk.tools import Arg
from .base import GitHubCliTool
from kubiya_sdk.tools.registry import tool_registry

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

create_branch = GitHubCliTool(
    name="github_create_branch",
    description="Create a new branch in a GitHub repository",
    content="""
echo "🌱 Creating new branch in repository..."
echo "📂 Repository: ${repo}"
echo "🔖 New branch: ${branch_name}"
echo "🔗 Base branch: ${base_branch:-main}"

# Validate repository exists
if ! gh repo view "${repo}" &>/dev/null; then
    echo "❌ Repository ${repo} not found or not accessible"
    exit 1
fi

# Create branch
if gh api --method POST "repos/${repo}/git/refs" \
    -f ref="refs/heads/${branch_name}" \
    -f sha="$(gh api repos/${repo}/git/refs/heads/${base_branch:-main} --jq .object.sha)"; then
    echo "✅ Branch '${branch_name}' created successfully!"
    echo "🔗 Branch URL: https://github.com/${repo}/tree/${branch_name}"
else
    echo "❌ Failed to create branch"
    exit 1
fi
""",
    args=[
        Arg(name="repo", type="str", description="Repository name (owner/repo)", required=True),
        Arg(name="branch_name", type="str", description="Name for the new branch", required=True),
        Arg(name="base_branch", type="str", description="Base branch to create from (default: main)", required=False, default="main"),
    ],
)

REPO_TOOLS = [
    repo_create,
    create_branch
]

# Register all repo tools
for tool in REPO_TOOLS:
    tool_registry.register("github", tool)

__all__ = ['repo_create', 'create_branch']