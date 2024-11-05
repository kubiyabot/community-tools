from kubiya_sdk.tools import Arg
from .base import GitHubCliTool
from kubiya_sdk.tools.registry import tool_registry

repo_create = GitHubCliTool(
    name="github_repo_create",
    description="Create a new GitHub repository with specified name, organization, visibility, description, and homepage.",
    content="""
    REPO_NAME="$([[ -n "$org" ]] && echo "$org/$name" || echo "$name")"

    gh repo create "$REPO_NAME" \
        $([[ "$private" == "true" ]] && echo "--private" || echo "--public") \
        $([[ -n "$description" ]] && echo "--description \"$description\"") \
        $([[ -n "$homepage" ]] && echo "--homepage $homepage")
    """,
    args=[
        Arg(name="name", type="str", description="New repository name. Example: 'my-awesome-project'", required=True),
        Arg(name="org", type="str", description="Optional organization name if creating under an org. Example: 'my-organization'", required=False),
        Arg(name="private", type="bool", description="Create as private repository. Set to true for private, false for public. Example: true", required=False),
        Arg(name="description", type="str", description="Repository description. Example: 'This project does amazing things'", required=False),
        Arg(name="homepage", type="str", description="Repository homepage URL. Example: 'https://myproject.com'", required=False),
    ],
)

repo_clone = GitHubCliTool(
    name="github_repo_clone",
    description="Clone a GitHub repository to your local machine.",
    content="gh repo clone $repo",
    args=[Arg(name="repo", type="str", description="Repository name or URL to clone. Example: 'octocat/Hello-World' or 'https://github.com/octocat/Hello-World.git'", required=True)],
)

repo_view = GitHubCliTool(
    name="github_repo_view",
    description="View details of a GitHub repository, optionally opening it in a web browser.",
    content="gh repo view $repo $([[ \"$web\" == \"true\" ]] && echo \"--web\")",
    args=[
        Arg(name="repo", type="str", description="Repository name or URL to view. Example: 'octocat/Hello-World'", required=True),
        Arg(name="web", type="bool", description="Open repository in web browser instead of showing info in terminal. Example: true", required=False),
    ],
)

repo_list = GitHubCliTool(
    name="github_repo_list",
    description="List GitHub repositories for the authenticated user, with options to limit results and filter by visibility.",
    content="gh repo list $([[ -n \"$limit\" ]] && echo \"--limit $limit\") $([[ -n \"$visibility\" ]] && echo \"--$visibility\")",
    args=[
        Arg(name="limit", type="int", description="Maximum number of repositories to list. Example: 10", required=False),
        Arg(name="visibility", type="str", description="Filter repositories by visibility (public, private, or internal). Example: 'public'", required=False),
    ],
)

repo_delete = GitHubCliTool(
    name="github_repo_delete",
    description="Delete a GitHub repository. Use with caution as this action is irreversible.",
    content="gh repo delete $repo --yes",
    args=[Arg(name="repo", type="str", description="Repository name or URL to delete. Example: 'myusername/old-project'", required=True)],
)

repo_fork = GitHubCliTool(
    name="github_repo_fork",
    description="Fork a GitHub repository to your account, with an option to clone it locally.",
    content="gh repo fork $repo $([[ \"$clone\" == \"true\" ]] && echo \"--clone\")",
    args=[
        Arg(name="repo", type="str", description="Repository name or URL to fork. Example: 'octocat/Spoon-Knife'", required=True),
        Arg(name="clone", type="bool", description="Clone the fork after forking. Example: true", required=False),
    ],
)

repo_archive = GitHubCliTool(
    name="github_repo_archive",
    description="Archive a GitHub repository, making it read-only.",
    content="gh repo archive $repo --yes",
    args=[Arg(name="repo", type="str", description="Repository name or URL to archive. Example: 'myusername/old-project'", required=True)],
)

repo_unarchive = GitHubCliTool(
    name="github_repo_unarchive",
    description="Unarchive a GitHub repository, making it editable again.",
    content="gh repo unarchive $repo --yes",
    args=[Arg(name="repo", type="str", description="Repository name or URL to unarchive. Example: 'myusername/old-project'", required=True)],
)

repo_readme = GitHubCliTool(
    name="github_repo_readme",
    description="View the README content of a GitHub repository.",
    content="gh repo view $repo --readme",
    args=[Arg(name="repo", type="str", description="Repository name or URL to view README. Example: 'octocat/Hello-World'", required=True)],
)

repo_language = GitHubCliTool(
    name="github_repo_language",
    description="Detect the primary programming language of a GitHub repository.",
    content="gh api repos/$repo/languages | jq -r 'to_entries | max_by(.value) | .key'",
    args=[Arg(name="repo", type="str", description="Repository name in 'owner/repo' format. Example: 'octocat/Hello-World'", required=True)],
)

repo_metadata = GitHubCliTool(
    name="github_repo_metadata",
    description="Fetch comprehensive metadata for a GitHub repository.",
    content="gh api repos/$repo | jq '{name, description, language, stargazers_count, forks_count, open_issues_count, created_at, updated_at, license: .license.name}'",
    args=[Arg(name="repo", type="str", description="Repository name in 'owner/repo' format. Example: 'octocat/Hello-World'", required=True)],
)

repo_search = GitHubCliTool(
    name="github_repo_search",
    description="Search for GitHub repositories based on various criteria.",
    content="gh search repos $query $([[ -n \"$limit\" ]] && echo \"--limit $limit\") $([[ -n \"$sort\" ]] && echo \"--sort $sort\")",
    args=[
        Arg(name="query", type="str", description="Search query for repositories. Example: 'tensorflow language:python'", required=True),
        Arg(name="limit", type="int", description="Maximum number of repositories to return. Example: 50", required=False),
        Arg(name="sort", type="str", description="Sort order for results (stars, forks, updated). Example: 'stars'", required=False),
    ],
)

github_search = GitHubCliTool(
    name="github_search",
    description="Perform a general GitHub search across different contexts (repositories, code, issues, pull requests).",
    content="gh search $type $query $([[ -n \"$limit\" ]] && echo \"--limit $limit\")",
    args=[
        Arg(name="type", type="str", description="Search type (repos, code, issues, prs). Example: 'code'", required=True),
        Arg(name="query", type="str", description="Search query. Example: 'function language:python'", required=True),
        Arg(name="limit", type="int", description="Maximum number of results to return. Example: 100", required=False),
    ],
)

github_actions_list = GitHubCliTool(
    name="github_actions_list",
    description="List all GitHub Actions workflows in a repository.",
    content="gh workflow list --repo $repo",
    args=[
        Arg(name="repo", type="str", description="Repository name in 'owner/repo' format. Example: 'octocat/Hello-World'", required=True),
    ],
)

github_actions_status = GitHubCliTool(
    name="github_actions_status",
    description="Get the status of a specific GitHub Actions workflow run.",
    content="gh run view --repo $repo $run_id",
    args=[
        Arg(name="repo", type="str", description="Repository name in 'owner/repo' format. Example: 'octocat/Hello-World'", required=True),
        Arg(name="run_id", type="str", description="Workflow run ID. Example: '1234567890'", required=True),
    ],
)

github_actions_logs = GitHubCliTool(
    name="github_actions_logs",
    description="Retrieve logs for a specific GitHub Actions workflow run.",
    content="gh run view --repo $repo $run_id --log",
    args=[
        Arg(name="repo", type="str", description="Repository name in 'owner/repo' format. Example: 'octocat/Hello-World'", required=True),
        Arg(name="run_id", type="str", description="Workflow run ID. Example: '1234567890'", required=True),
    ],
)

github_releases = GitHubCliTool(
    name="github_releases",
    description="List releases for a GitHub repository.",
    content="gh release list --repo $repo $([[ -n \"$limit\" ]] && echo \"--limit $limit\")",
    args=[
        Arg(name="repo", type="str", description="Repository name in 'owner/repo' format. Example: 'octocat/Hello-World'", required=True),
        Arg(name="limit", type="int", description="Maximum number of releases to list. Example: 10", required=False),
    ],
)

github_create_issue = GitHubCliTool(
    name="github_create_issue",
    description="Create a new issue in a GitHub repository.",
    content="gh issue create --repo $repo --title \"$title\" --body \"$body\"",
    args=[
        Arg(name="repo", type="str", description="Repository name in 'owner/repo' format. Example: 'octocat/Hello-World'", required=True),
        Arg(name="title", type="str", description="Issue title. Example: 'Bug: App crashes on startup'", required=True),
        Arg(name="body", type="str", description="Issue body content. Example: 'When launching the app, it immediately crashes. Steps to reproduce: 1. Install app 2. Open app 3. Observe crash'", required=True),
    ],
)

github_close_issue = GitHubCliTool(
    name="github_close_issue",
    description="Close an existing issue in a GitHub repository.",
    content="gh issue close $issue_number --repo $repo",
    args=[
        Arg(name="repo", type="str", description="Repository name in 'owner/repo' format. Example: 'octocat/Hello-World'", required=True),
        Arg(name="issue_number", type="int", description="Issue number to close. Example: 42", required=True),
    ],
)

# Register all tools
for tool in [
    repo_create, repo_clone, repo_view, repo_list, repo_delete, repo_fork,
    repo_archive, repo_unarchive, repo_readme, repo_language,
    repo_metadata, repo_search, github_search,
    github_actions_list, github_actions_status, github_actions_logs,
    github_releases, github_create_issue
]:
    tool_registry.register("github", tool)