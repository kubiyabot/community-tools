from kubiya_sdk.tools import Arg
from .base import GitHubCliTool
from kubiya_sdk.tools.registry import tool_registry

pr_create = GitHubCliTool(
    name="github_pr_create",
    description="Create a new pull request in a GitHub repository.",
    content="gh pr create --repo $repo --title \"$title\" --body \"$body\" --base $base --head $head",
    args=[
        Arg(name="repo", type="str", description="Repository name in 'owner/repo' format. Example: 'octocat/Hello-World'", required=True),
        Arg(name="title", type="str", description="Pull request title. Example: 'Add new feature: Dark mode'", required=True),
        Arg(name="body", type="str", description="Pull request description. Example: 'This PR adds a dark mode feature to the app. It includes new styles and a toggle in the settings menu.'", required=True),
        Arg(name="base", type="str", description="The branch you want your changes pulled into. Example: 'main'", required=True),
        Arg(name="head", type="str", description="The branch that contains commits for your pull request. Example: 'feature/dark-mode'", required=True),
    ],
)

pr_list = GitHubCliTool(
    name="github_pr_list",
    description="List pull requests in a GitHub repository.",
    content="gh pr list --repo $repo $([[ -n \"$state\" ]] && echo \"--state $state\") $([[ -n \"$limit\" ]] && echo \"--limit $limit\")",
    args=[
        Arg(name="repo", type="str", description="Repository name in 'owner/repo' format. Example: 'octocat/Hello-World'", required=True),
        Arg(name="state", type="str", description="Filter by pull request state (open, closed, merged, all). Example: 'open'", required=False),
        Arg(name="limit", type="int", description="Maximum number of pull requests to list. Example: 10", required=False),
    ],
)

pr_view = GitHubCliTool(
    name="github_pr_view",
    description="View details of a specific pull request.",
    content="gh pr view --repo $repo $number",
    args=[
        Arg(name="repo", type="str", description="Repository name in 'owner/repo' format. Example: 'octocat/Hello-World'", required=True),
        Arg(name="number", type="int", description="Pull request number. Example: 123", required=True),
    ],
)

pr_merge = GitHubCliTool(
    name="github_pr_merge",
    description="Merge a pull request.",
    content="gh pr merge --repo $repo $number --$merge_method",
    args=[
        Arg(name="repo", type="str", description="Repository name in 'owner/repo' format. Example: 'octocat/Hello-World'", required=True),
        Arg(name="number", type="int", description="Pull request number. Example: 123", required=True),
        Arg(name="merge_method", type="str", description="Merge method to use (merge, squash, rebase). Example: 'squash'", required=True),
    ],
)

pr_close = GitHubCliTool(
    name="github_pr_close",
    description="Close a pull request without merging.",
    content="gh pr close --repo $repo $number",
    args=[
        Arg(name="repo", type="str", description="Repository name in 'owner/repo' format. Example: 'octocat/Hello-World'", required=True),
        Arg(name="number", type="int", description="Pull request number. Example: 123", required=True),
    ],
)

pr_comment = GitHubCliTool(
    name="github_pr_comment",
    description="Add a comment to a pull request.",
    content="gh pr comment --repo $repo $number --body \"$body\"",
    args=[
        Arg(name="repo", type="str", description="Repository name in 'owner/repo' format. Example: 'octocat/Hello-World'", required=True),
        Arg(name="number", type="int", description="Pull request number. Example: 123", required=True),
        Arg(name="body", type="str", description="Comment text. Example: 'Great work! Just a few minor suggestions.'", required=True),
    ],
)

pr_review = GitHubCliTool(
    name="github_pr_review",
    description="Add a review to a pull request.",
    content="gh pr review --repo $repo $number --$review_type $([[ -n \"$body\" ]] && echo \"--body \\\"$body\\\"\")",
    args=[
        Arg(name="repo", type="str", description="Repository name in 'owner/repo' format. Example: 'octocat/Hello-World'", required=True),
        Arg(name="number", type="int", description="Pull request number. Example: 123", required=True),
        Arg(name="review_type", type="str", description="Type of review (approve, request-changes, comment). Example: 'approve'", required=True),
        Arg(name="body", type="str", description="Review comment. Example: 'LGTM! Approved with some minor suggestions.'", required=False),
    ],
)

pr_diff = GitHubCliTool(
    name="github_pr_diff",
    description="View the diff of a pull request.",
    content="gh pr diff --repo $repo $number",
    args=[
        Arg(name="repo", type="str", description="Repository name in 'owner/repo' format. Example: 'octocat/Hello-World'", required=True),
        Arg(name="number", type="int", description="Pull request number. Example: 123", required=True),
    ],
)

pr_checkout = GitHubCliTool(
    name="github_pr_checkout",
    description="Check out a pull request locally.",
    content="gh pr checkout --repo $repo $number",
    args=[
        Arg(name="repo", type="str", description="Repository name in 'owner/repo' format. Example: 'octocat/Hello-World'", required=True),
        Arg(name="number", type="int", description="Pull request number. Example: 123", required=True),
    ],
)

pr_ready = GitHubCliTool(
    name="github_pr_ready",
    description="Mark a pull request as ready for review.",
    content="gh pr ready --repo $repo $number",
    args=[
        Arg(name="repo", type="str", description="Repository name in 'owner/repo' format. Example: 'octocat/Hello-World'", required=True),
        Arg(name="number", type="int", description="Pull request number. Example: 123", required=True),
    ],
)

pr_checks = GitHubCliTool(
    name="github_pr_checks",
    description="View status checks for a pull request.",
    content="gh pr checks --repo $repo $number",
    args=[
        Arg(name="repo", type="str", description="Repository name in 'owner/repo' format. Example: 'octocat/Hello-World'", required=True),
        Arg(name="number", type="int", description="Pull request number. Example: 123", required=True),
    ],
)

pr_files = GitHubCliTool(
    name="github_pr_files",
    description="List files changed in a pull request.",
    content="gh pr view --repo $repo $number --files",
    args=[
        Arg(name="repo", type="str", description="Repository name in 'owner/repo' format. Example: 'octocat/Hello-World'", required=True),
        Arg(name="number", type="int", description="Pull request number. Example: 123", required=True),
    ],
)

# Add these new tools at the end of the file

github_graphql = GitHubCliTool(
    name="github_graphql",
    description="Execute a custom GraphQL query against the GitHub API.",
    content="""
    echo '$query' | gh api graphql -f query=@- $([[ -n "$variables" ]] && echo "--raw-field $variables")
    """,
    args=[
        Arg(name="query", type="str", description="GraphQL query to execute. Example: 'query { viewer { login } }'", required=True),
        Arg(name="variables", type="str", description="JSON string of variables for the GraphQL query. Example: '{\"owner\": \"octocat\", \"name\": \"Hello-World\"}'", required=False),
    ],
)

github_rest = GitHubCliTool(
    name="github_rest",
    description="Make a custom REST API request to GitHub.",
    content="""
    gh api $endpoint $([[ -n "$method" ]] && echo "-X $method") $([[ -n "$data" ]] && echo "-f $data")
    """,
    args=[
        Arg(name="endpoint", type="str", description="REST API endpoint. Example: '/repos/octocat/Hello-World'", required=True),
        Arg(name="method", type="str", description="HTTP method (GET, POST, PATCH, DELETE, etc.). Default is GET. Example: 'POST'", required=False),
        Arg(name="data", type="str", description="JSON string of data to send with the request. Example: '{\"name\": \"new-repo-name\"}'", required=False),
    ],
)

# Register the new tools
tool_registry.register("github", github_graphql)
tool_registry.register("github", github_rest)

# Update the __all__ list to include the new tools
__all__ = ['pr_create', 'pr_list', 'pr_view', 'pr_merge', 'pr_close', 'pr_comment', 'pr_review', 'pr_diff', 'pr_checkout', 'pr_ready', 'pr_checks', 'pr_files', 'github_graphql', 'github_rest']