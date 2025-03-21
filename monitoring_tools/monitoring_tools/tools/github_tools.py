from .base import GitHubBaseTool
from kubiya_sdk.tools import Arg
from kubiya_sdk.tools.registry import tool_registry

class GitHubTools:
    """GitHub repository investigation tools."""
    
    def __init__(self):
        """Initialize and register all GitHub tools."""
        tools = [
            self.get_recent_commits(),
            self.get_pull_requests(),
            self.get_workflow_runs(),
            self.search_issues()
        ]
        
        for tool in tools:
            tool_registry.register("github", tool)

    def get_recent_commits(self) -> GitHubBaseTool:
        """Get recent commits for a repository."""
        return GitHubBaseTool(
            name="get_recent_commits",
            description="Get recent commits for a GitHub repository",
            content="""
            if [ -z "$repo" ]; then
                echo "Error: Repository name is required"
                exit 1
            fi

            # Configure GitHub CLI
            echo "$GITHUB_TOKEN" | gh auth login --with-token

            # Get recent commits
            gh api \
              -H "Accept: application/vnd.github.v3+json" \
              "/repos/$repo/commits" \
              --jq '[.[] | {
                sha: .sha,
                author: .commit.author.name,
                date: .commit.author.date,
                message: .commit.message,
                url: .html_url
              }]'
            """,
            args=[
                Arg(name="repo",
                    description="Repository name (owner/repo)",
                    required=True),
                Arg(name="limit",
                    description="Number of commits to return",
                    required=False)
            ]
        )

    def get_pull_requests(self) -> GitHubBaseTool:
        """Get pull requests for a repository."""
        return GitHubBaseTool(
            name="get_pull_requests",
            description="Get pull requests for a GitHub repository",
            content="""
            if [ -z "$repo" ]; then
                echo "Error: Repository name is required"
                exit 1
            fi

            # Configure GitHub CLI
            echo "$GITHUB_TOKEN" | gh auth login --with-token

            # Get pull requests using GitHub CLI
            gh pr list -R "$repo" \
                --json number,title,author,createdAt,updatedAt,state,isDraft,url \
                --jq '.[] | {
                    number: .number,
                    title: .title,
                    user: .author.login,
                    created_at: .createdAt,
                    updated_at: .updatedAt,
                    state: .state,
                    draft: .isDraft,
                    url: .url
                }'
            """,
            args=[
                Arg(name="repo",
                    description="Repository name (owner/repo)",
                    required=True),
                Arg(name="state",
                    description="PR state (open/closed/all)",
                    required=False),
                Arg(name="labels",
                    description="Comma-separated list of labels",
                    required=False)
            ]
        )

    def get_workflow_runs(self) -> GitHubBaseTool:
        """Get recent workflow runs for a repository."""
        return GitHubBaseTool(
            name="get_workflow_runs",
            description="Get recent GitHub Actions workflow runs",
            content="""
            if [ -z "$repo" ]; then
                echo "Error: Repository name is required"
                exit 1
            fi

            # Configure GitHub CLI
            echo "$GITHUB_TOKEN" | gh auth login --with-token

            # Get workflow runs using GitHub CLI
            gh run list -R "$repo" \
                --limit ${limit:-10} \
                --json databaseId,name,status,conclusion,headBranch,createdAt,updatedAt,url \
                --jq '.[] | {
                    id: .databaseId,
                    name: .name,
                    status: .status,
                    conclusion: .conclusion,
                    branch: .headBranch,
                    created_at: .createdAt,
                    updated_at: .updatedAt,
                    url: .url
                }'
            """,
            args=[
                Arg(name="repo",
                    description="Repository name (owner/repo)",
                    required=True),
                Arg(name="limit",
                    description="Number of runs to return",
                    required=False)
            ]
        )

    def search_issues(self) -> GitHubBaseTool:
        """Search issues and pull requests."""
        return GitHubBaseTool(
            name="search_issues",
            description="Search GitHub issues and pull requests",
            content="""
            if [ -z "$query" ]; then
                echo "Error: Search query is required"
                exit 1
            fi

            # Configure GitHub CLI
            echo "$GITHUB_TOKEN" | gh auth login --with-token

            # Search issues using GitHub CLI
            gh issue list -R "$repo" \
                --search "$query" \
                --json number,title,state,createdAt,updatedAt,repository,url,labels \
                --jq '.[] | {
                    number: .number,
                    title: .title,
                    state: .state,
                    created_at: .createdAt,
                    updated_at: .updatedAt,
                    repository: .repository.url,
                    url: .url,
                    labels: [.labels[].name]
                }'
            """,
            args=[
                Arg(name="query",
                    description="Search query",
                    required=True),
                Arg(name="sort",
                    description="Sort field (created/updated/comments)",
                    required=False),
                Arg(name="order",
                    description="Sort order (asc/desc)",
                    required=False)
            ]
        )

# Initialize when module is imported
GitHubTools() 