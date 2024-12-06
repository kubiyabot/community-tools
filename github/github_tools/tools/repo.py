from kubiya_sdk.tools import Arg
from .base import GitHubCliTool
from kubiya_sdk.tools.registry import tool_registry

repo_create = GitHubCliTool(
    name="github_repo_create", 
    description="Create a new GitHub repository with specified name, organization, visibility, description, and homepage.",
    content="""
    echo "🚀 Creating new GitHub repository..."
    echo "📝 Name: $name"
    [[ -n "$org" ]] && echo "🏢 Organization: $org"
    [[ "$private" == "true" ]] && echo "🔒 Visibility: Private" || echo "🌎 Visibility: Public"
    [[ -n "$description" ]] && echo "📄 Description: $description"
    [[ -n "$homepage" ]] && echo "🔗 Homepage: $homepage"

    REPO_NAME="$([[ -n "$org" ]] && echo "$org/$name" || echo "$name")"

    if ! gh repo create "$REPO_NAME" \
        $([[ "$private" == "true" ]] && echo "--private" || echo "--public") \
        $([[ -n "$description" ]] && echo "--description \"$description\"") \
        $([[ -n "$homepage" ]] && echo "--homepage $homepage"); then
        echo "❌ Failed to create repository. Common issues:"
        echo "  • Repository name '$name' may already exist"
        echo "  • You may not have permission to create repositories in organization '$org'"
        echo "  • Your GitHub token may not have the required scopes"
        echo "🔍 Suggestions:"
        echo "  • Try a different repository name"
        echo "  • Verify organization permissions"
        echo "  • Check your GitHub token has 'repo' scope"
        exit 1
    fi
        
    echo "✨ Repository created successfully!"
    echo "🔗 Repository URL: https://github.com/$REPO_NAME"
    """,
    args=[
        Arg(name="name", type="str", description="New repository name. Example: 'my-awesome-project'", required=True),
        Arg(name="org", type="str", description="Optional organization name if creating under an org. Example: 'my-organization'", required=False),
        Arg(name="private", type="bool", description="Create as private repository. Set to true for private, false for public. Example: true", required=False),
        Arg(name="description", type="str", description="Repository description. Example: 'This project does amazing things'", required=False),
        Arg(name="homepage", type="str", description="Repository homepage URL. Example: 'https://myproject.com'", required=False),
    ],
)
repo_view = GitHubCliTool(
    name="github_repo_view",
    description="View detailed information about a GitHub repository.",
    content="""
    echo "🔍 Fetching repository details for $repo..."
    echo "🔗 Repository URL: https://github.com/$repo"
    
    # Get repository details in JSON format
    if ! DETAILS=$(gh repo view $repo --json name,description,visibility,defaultBranch,createdAt,updatedAt,pushedAt,diskUsage,language,hasIssues,hasProjects,hasWiki,isArchived,stargazerCount,forkCount); then
        echo "❌ Failed to fetch repository details. Common issues:"
        echo "  • Repository '$repo' may not exist"
        echo "  • You may not have access to this repository"
        echo "  • Repository name format may be incorrect"
        echo "🔍 Suggestions:"
        echo "  • Verify the repository exists at https://github.com/$repo"
        echo "  • Check your access permissions"
        echo "  • Use format 'owner/repo' (e.g. 'octocat/Hello-World')"
        exit 1
    fi
    
    # Parse and display details nicely
    echo "📊 Repository Details:"
    echo "📝 Name: $(echo $DETAILS | jq -r .name)"
    echo "📄 Description: $(echo $DETAILS | jq -r .description)"
    echo "🔒 Visibility: $(echo $DETAILS | jq -r .visibility)"
    echo "🌿 Default Branch: $(echo $DETAILS | jq -r .defaultBranch)"
    echo "📅 Created: $(echo $DETAILS | jq -r .createdAt)"
    echo "🔄 Last Updated: $(echo $DETAILS | jq -r .updatedAt)"
    echo "⬆️ Last Push: $(echo $DETAILS | jq -r .pushedAt)"
    echo "💾 Size: $(echo $DETAILS | jq -r .diskUsage)KB"
    echo "💻 Primary Language: $(echo $DETAILS | jq -r .language)"
    echo "⭐ Stars: $(echo $DETAILS | jq -r .stargazerCount)"
    echo "🍴 Forks: $(echo $DETAILS | jq -r .forkCount)"
    echo "📌 Features:"
    echo "  • Issues: $(echo $DETAILS | jq -r .hasIssues)"
    echo "  • Projects: $(echo $DETAILS | jq -r .hasProjects)" 
    echo "  • Wiki: $(echo $DETAILS | jq -r .hasWiki)"
    echo "  • Archived: $(echo $DETAILS | jq -r .isArchived)"
    
    echo "✨ Repository details retrieved successfully!"
    """,
    args=[
        Arg(name="repo", type="str", description="Repository name or URL to view. Example: 'octocat/Hello-World'", required=True),
    ],
)

repo_list = GitHubCliTool(
    name="github_repo_list",
    description="List GitHub repositories for the authenticated user, with options to limit results and filter by visibility.",
    content="""
    echo "📋 Listing GitHub repositories..."
    [[ -n "$limit" ]] && echo "🔢 Limit: $limit repositories"
    [[ -n "$visibility" ]] && echo "👁️ Filtering by visibility: $visibility"
    echo "📚 Documentation: https://docs.github.com/en/repositories"
    
    if ! gh repo list $([[ -n "$limit" ]] && echo "--limit $limit") $([[ -n "$visibility" ]] && echo "--$visibility"); then
        echo "❌ Failed to list repositories. Common issues:"
        echo "  • Invalid visibility filter (must be 'public', 'private', or 'internal')"
        echo "  • GitHub token may be invalid or expired"
        echo "  • Network connectivity issues"
        echo "🔍 Suggestions:"
        echo "  • Check visibility parameter is correct"
        echo "  • Verify your GitHub authentication of the running Kubiya agent"
        exit 1
    fi
    
    echo "✨ Repository list retrieved successfully!"
    """,
    args=[
        Arg(name="limit", type="int", description="Maximum number of repositories to list. Example: 10", required=False),
        Arg(name="visibility", type="str", description="Filter repositories by visibility (public, private, or internal). Example: 'public'", required=False),
    ],
)

repo_delete = GitHubCliTool(
    name="github_repo_delete",
    description="Delete a GitHub repository. Use with caution as this action is irreversible.",
    content="""
    echo "⚠️ WARNING: About to delete repository $repo"
    echo "❗ This action is irreversible!"
    echo "🔗 Repository URL to be deleted: https://github.com/$repo"
    echo "🗑️ Proceeding with deletion..."
    
    if ! gh repo delete $repo --yes; then
        echo "❌ Failed to delete repository. Common issues:"
        echo "  • Repository '$repo' may not exist"
        echo "  • You may not have permission to delete this repository"
        echo "  • Repository may be already deleted"
        echo "🔍 Suggestions:"
        echo "  • Verify you have admin access to the repository"
        echo "  • Check if repository still exists"
        echo "  • Contact repository owner for permissions"
        exit 1
    fi
    
    echo "✅ Repository deleted successfully!"
    """,
    args=[Arg(name="repo", type="str", description="Repository name or URL to delete. Example: 'myusername/old-project'", required=True)],
)

repo_fork = GitHubCliTool(
    name="github_repo_fork",
    description="Fork a GitHub repository to your account, with an option to clone it locally.",
    content="""
    echo "🍴 Forking repository $repo..."
    echo "🔗 Original repository: https://github.com/$repo"
    [[ "$clone" == "true" ]] && echo "📥 Will clone locally after forking"
    
    if ! gh repo fork $repo $([[ "$clone" == "true" ]] && echo "--clone"); then
        echo "❌ Failed to fork repository. Common issues:"
        echo "  • Repository '$repo' may not exist"
        echo "  • You may already have a fork of this repository"
        echo "  • Repository may not allow forking"
        echo "🔍 Suggestions:"
        echo "  • Verify repository exists and allows forking"
        echo "  • Check if you already have a fork"
        echo "  • Contact repository owner"
        exit 1
    fi
    
    FORK_USER=$(gh api user -q .login)
    echo "✨ Repository forked successfully!"
    echo "🔗 Forked repository URL: https://github.com/$FORK_USER/$(echo $repo | cut -d'/' -f2)"
    [[ "$clone" == "true" ]] && echo "📁 Local clone is ready!"
    """,
    args=[
        Arg(name="repo", type="str", description="Repository name or URL to fork. Example: 'octocat/Spoon-Knife'", required=True),
        Arg(name="clone", type="bool", description="Clone the fork after forking. Example: true", required=False),
    ],
)

repo_archive = GitHubCliTool(
    name="github_repo_archive",
    description="Archive a GitHub repository, making it read-only.",
    content="""
    echo "📦 Archiving repository $repo..."
    echo "🔗 Repository URL: https://github.com/$repo"
    echo "🔒 This will make the repository read-only"
    echo "📚 Learn more: https://docs.github.com/en/repositories/archiving-a-github-repository"
    
    if ! gh repo archive $repo --yes; then
        echo "❌ Failed to archive repository. Common issues:"
        echo "  • Repository '$repo' may not exist"
        echo "  • You may not have admin access"
        echo "  • Repository may already be archived"
        echo "🔍 Suggestions:"
        echo "  • Verify you have admin access"
        echo "  • Check repository status"
        echo "  • Contact repository owner"
        exit 1
    fi
    
    echo "✨ Repository archived successfully!"
    """,
    args=[Arg(name="repo", type="str", description="Repository name or URL to archive. Example: 'myusername/old-project'", required=True)],
)

repo_unarchive = GitHubCliTool(
    name="github_repo_unarchive",
    description="Unarchive a GitHub repository, making it editable again.",
    content="""
    echo "📤 Unarchiving repository $repo..."
    echo "🔗 Repository URL: https://github.com/$repo"
    echo "🔓 This will make the repository editable again"
    
    if ! gh repo unarchive $repo --yes; then
        echo "❌ Failed to unarchive repository. Common issues:"
        echo "  • Repository '$repo' may not exist"
        echo "  • You may not have admin access"
        echo "  • Repository may not be archived"
        echo "🔍 Suggestions:"
        echo "  • Verify you have admin access"
        echo "  • Check if repository is actually archived"
        echo "  • Contact repository owner"
        exit 1
    fi
    
    echo "✨ Repository unarchived successfully!"
    """,
    args=[Arg(name="repo", type="str", description="Repository name or URL to unarchive. Example: 'myusername/old-project'", required=True)],
)

repo_readme = GitHubCliTool(
    name="github_repo_readme",
    description="View the README content of a GitHub repository.",
    content="""
    echo "📖 Fetching README for $repo..."
    echo "🔗 Repository URL: https://github.com/$repo"
    echo "🔗 Raw README URL: https://raw.githubusercontent.com/$repo/main/README.md"
    
    if ! gh repo view $repo --readme; then
        echo "❌ Failed to fetch README. Common issues:"
        echo "  • Repository '$repo' may not exist"
        echo "  • Repository may not have a README file"
        echo "  • You may not have access to this repository"
        echo "🔍 Suggestions:"
        echo "  • Verify repository exists"
        echo "  • Check if README exists in repository"
        echo "  • Verify your access permissions"
        exit 1
    fi
    
    echo "✨ README content displayed successfully!"
    """,
    args=[Arg(name="repo", type="str", description="Repository name or URL to view README. Example: 'octocat/Hello-World'", required=True)],
)

repo_language = GitHubCliTool(
    name="github_repo_language",
    description="Detect the primary programming language of a GitHub repository.",
    content="""
    echo "🔍 Detecting primary language for $repo..."
    echo "🔗 Repository URL: https://github.com/$repo"
    
    if ! LANG=$(gh api repos/$repo/languages | jq -r 'to_entries | max_by(.value) | .key'); then
        echo "❌ Failed to detect language. Common issues:"
        echo "  • Repository '$repo' may not exist"
        echo "  • Repository may be empty"
        echo "  • API rate limit exceeded"
        echo "🔍 Suggestions:"
        echo "  • Verify repository exists and has code"
        echo "  • Wait if rate limited"
        echo "  • Check your access permissions"
        exit 1
    fi
    
    echo "📊 Primary language: $LANG"
    echo "🔗 Language trends: https://github.com/$repo/search?l=$LANG"
    
    echo "✨ Language detection completed!"
    """,
    args=[Arg(name="repo", type="str", description="Repository name in 'owner/repo' format. Example: 'octocat/Hello-World'", required=True)],
)

repo_metadata = GitHubCliTool(
    name="github_repo_metadata",
    description="Fetch comprehensive metadata for a GitHub repository.",
    content="""
    echo "📊 Fetching metadata for $repo..."
    echo "🔗 Repository URL: https://github.com/$repo"
    echo "🔗 API endpoint: https://api.github.com/repos/$repo"
    
    if ! gh api repos/$repo | jq '{name, description, language, stargazers_count, forks_count, open_issues_count, created_at, updated_at, license: .license.name}'; then
        echo "❌ Failed to fetch metadata. Common issues:"
        echo "  • Repository '$repo' may not exist"
        echo "  • API rate limit exceeded"
        echo "  • Network connectivity issues"
        echo "🔍 Suggestions:"
        echo "  • Verify repository exists"
        echo "  • Wait if rate limited"
        echo "  • Check your internet connection"
        exit 1
    fi
    
    echo "✨ Metadata retrieved successfully!"
    """,
    args=[Arg(name="repo", type="str", description="Repository name in 'owner/repo' format. Example: 'octocat/Hello-World'", required=True)],
)

repo_search = GitHubCliTool(
    name="github_repo_search",
    description="Search for GitHub repositories based on various criteria.",
    content="""
    echo "🔍 Searching repositories..."
    echo "🔎 Query: $query"
    [[ -n "$limit" ]] && echo "🔢 Limit: $limit results"
    [[ -n "$sort" ]] && echo "📊 Sorting by: $sort"
    echo "📚 Search syntax guide: https://docs.github.com/en/search-github/searching-on-github/searching-for-repositories"
    
    if ! gh search repos $query $([[ -n "$limit" ]] && echo "--limit $limit") $([[ -n "$sort" ]] && echo "--sort $sort"); then
        echo "❌ Search failed. Common issues:"
        echo "  • Invalid search syntax"
        echo "  • No results found"
        echo "  • API rate limit exceeded"
        echo "🔍 Suggestions:"
        echo "  • Check search syntax in documentation"
        echo "  • Try different search terms"
        echo "  • Wait if rate limited"
        exit 1
    fi
    
    echo "✨ Search completed successfully!"
    echo "🔗 View results on web: https://github.com/search?q=$query&type=repositories"
    """,
    args=[
        Arg(name="query", type="str", description="Search query for repositories. Example: 'tensorflow language:python'", required=True),
        Arg(name="limit", type="int", description="Maximum number of repositories to return. Example: 50", required=False),
        Arg(name="sort", type="str", description="Sort order for results (stars, forks, updated). Example: 'stars'", required=False),
    ],
)

github_search = GitHubCliTool(
    name="github_search",
    description="Perform a general GitHub search across different contexts (repositories, code, issues, pull requests).",
    content="""
    echo "🔍 Performing GitHub search..."
    echo "🎯 Type: $type"
    echo "🔎 Query: $query"
    [[ -n "$limit" ]] && echo "🔢 Limit: $limit results"
    echo "📚 Advanced search: https://github.com/search/advanced"
    
    if ! gh search $type $query $([[ -n "$limit" ]] && echo "--limit $limit"); then
        echo "❌ Search failed. Common issues:"
        echo "  • Invalid search type (must be repos, code, issues, or prs)"
        echo "  • Invalid search syntax"
        echo "  • API rate limit exceeded"
        echo "🔍 Suggestions:"
        echo "  • Verify search type is correct"
        echo "  • Check search syntax in documentation"
        echo "  • Wait if rate limited"
        exit 1
    fi
    
    echo "✨ Search completed successfully!"
    echo "🔗 View results on web: https://github.com/search?q=$query&type=$type"
    """,
    args=[
        Arg(name="type", type="str", description="Search type (repos, code, issues, prs). Example: 'code'", required=True),
        Arg(name="query", type="str", description="Search query. Example: 'function language:python'", required=True),
        Arg(name="limit", type="int", description="Maximum number of results to return. Example: 100", required=False),
    ],
)

github_actions_list = GitHubCliTool(
    name="github_actions_list",
    description="List all GitHub Actions workflows in a repository.",
    content="""
    echo "📋 Listing GitHub Actions workflows for $repo..."
    echo "🔗 Repository URL: https://github.com/$repo"
    echo "🔗 Actions tab: https://github.com/$repo/actions"
    
    if ! gh workflow list --repo $repo; then
        echo "❌ Failed to list workflows. Common issues:"
        echo "  • Repository '$repo' may not exist"
        echo "  • Repository may not have any workflows"
        echo "  • You may not have access to workflows"
        echo "🔍 Suggestions:"
        echo "  • Verify repository exists"
        echo "  • Check if workflows are configured"
        echo "  • Verify your access permissions"
        exit 1
    fi
    
    echo "✨ Workflow list retrieved successfully!"
    """,
    args=[
        Arg(name="repo", type="str", description="Repository name in 'owner/repo' format. Example: 'octocat/Hello-World'", required=True),
    ],
)

github_actions_status = GitHubCliTool(
    name="github_actions_status",
    description="Get the status of a specific GitHub Actions workflow run.",
    content="""
    echo "🔍 Checking workflow run status..."
    echo "📦 Repository: $repo"
    echo "🔢 Run ID: $run_id"
    echo "🔗 Run URL: https://github.com/$repo/actions/runs/$run_id"
    
    if ! gh run view --repo $repo $run_id; then
        echo "❌ Failed to get workflow status. Common issues:"
        echo "  • Run ID '$run_id' may not exist"
        echo "  • Repository '$repo' may not exist"
        echo "  • You may not have access to this workflow"
        echo "🔍 Suggestions:"
        echo "  • Verify run ID is correct"
        echo "  • Check repository exists"
        echo "  • Verify your access permissions"
        exit 1
    fi
    
    echo "✨ Status check completed!"
    """,
    args=[
        Arg(name="repo", type="str", description="Repository name in 'owner/repo' format. Example: 'octocat/Hello-World'", required=True),
        Arg(name="run_id", type="str", description="Workflow run ID. Example: '1234567890'", required=True),
    ],
)

github_actions_logs = GitHubCliTool(
    name="github_actions_logs",
    description="Retrieve logs for a specific GitHub Actions workflow run.",
    content="""
    echo "📃 Fetching workflow run logs..."
    echo "📦 Repository: $repo"
    echo "🔢 Run ID: $run_id"
    echo "🔗 Run URL: https://github.com/$repo/actions/runs/$run_id"
    
    if ! gh run view --repo $repo $run_id --log; then
        echo "❌ Failed to fetch workflow logs. Common issues:"
        echo "  • Run ID '$run_id' may not exist"
        echo "  • Logs may have expired"
        echo "  • You may not have access to logs"
        echo "🔍 Suggestions:"
        echo "  • Verify run ID is correct"
        echo "  • Check if logs are still available"
        echo "  • Verify your access permissions"
        exit 1
    fi
    
    echo "✨ Logs retrieved successfully!"
    """,
    args=[
        Arg(name="repo", type="str", description="Repository name in 'owner/repo' format. Example: 'octocat/Hello-World'", required=True),
        Arg(name="run_id", type="str", description="Workflow run ID. Example: '1234567890'", required=True),
    ],
)

github_releases = GitHubCliTool(
    name="github_releases",
    description="List releases for a GitHub repository.",
    content="""
    echo "📋 Listing releases for $repo..."
    echo "🔗 Repository URL: https://github.com/$repo"
    echo "🔗 Releases page: https://github.com/$repo/releases"
    [[ -n "$limit" ]] && echo "🔢 Limit: $limit releases"
    
    if ! gh release list --repo $repo $([[ -n "$limit" ]] && echo "--limit $limit"); then
        echo "❌ Failed to list releases. Common issues:"
        echo "  • Repository '$repo' may not exist"
        echo "  • Repository may not have any releases"
        echo "  • You may not have access to this repository"
        echo "🔍 Suggestions:"
        echo "  • Verify repository exists"
        echo "  • Check if repository has releases"
        echo "  • Verify your access permissions"
        exit 1
    fi
    
    echo "✨ Release list retrieved successfully!"
    """,
    args=[
        Arg(name="repo", type="str", description="Repository name in 'owner/repo' format. Example: 'octocat/Hello-World'", required=True),
        Arg(name="limit", type="int", description="Maximum number of releases to list. Example: 10", required=False),
    ],
)

github_create_issue = GitHubCliTool(
    name="github_create_issue",
    description="Create a new issue in a GitHub repository.",
    content="""
    echo "📝 Creating new issue..."
    echo "📦 Repository: $repo"
    echo "📌 Title: $title"
    echo "🔗 Issues page: https://github.com/$repo/issues"
    
    if ! ISSUE_URL=$(gh issue create --repo $repo --title "$title" --body "$body" --json url -q .url); then
        echo "❌ Failed to create issue. Common issues:"
        echo "  • Repository '$repo' may not exist"
        echo "  • Issues may be disabled for this repository"
        echo "  • You may not have permission to create issues"
        echo "🔍 Suggestions:"
        echo "  • Verify repository exists"
        echo "  • Check if issues are enabled"
        echo "  • Verify your access permissions"
        exit 1
    fi
    
    echo "✨ Issue created successfully!"
    echo "🔗 Issue URL: $ISSUE_URL"
    """,
    args=[
        Arg(name="repo", type="str", description="Repository name in 'owner/repo' format. Example: 'octocat/Hello-World'", required=True),
        Arg(name="title", type="str", description="Issue title. Example: 'Bug: App crashes on startup'", required=True),
        Arg(name="body", type="str", description="Issue body content. Example: 'When launching the app, it immediately crashes. Steps to reproduce: 1. Install app 2. Open app 3. Observe crash'", required=True),
    ],
)

github_close_issue = GitHubCliTool(
    name="github_close_issue",
    description="Close an existing issue in a GitHub repository.",
    content="""
    echo "🔒 Closing issue #$issue_number..."
    echo "📦 Repository: $repo"
    echo "🔗 Issue URL: https://github.com/$repo/issues/$issue_number"
    
    if ! gh issue close $issue_number --repo $repo; then
        echo "❌ Failed to close issue. Common issues:"
        echo "  • Issue #$issue_number may not exist"
        echo "  • Issue may already be closed"
        echo "  • You may not have permission to close issues"
        echo "🔍 Suggestions:"
        echo "  • Verify issue exists"
        echo "  • Check if issue is already closed"
        echo "  • Verify your access permissions"
        exit 1
    fi
    
    echo "✨ Issue closed successfully!"
    """,
    args=[
        Arg(name="repo", type="str", description="Repository name in 'owner/repo' format. Example: 'octocat/Hello-World'", required=True),
        Arg(name="issue_number", type="int", description="Issue number to close. Example: 42", required=True),
    ],
)

# Register all tools
for tool in [
    repo_create, repo_view, repo_list, repo_delete, repo_fork,
    repo_archive, repo_unarchive, repo_readme, repo_language,
    repo_metadata, repo_search, github_search,
    github_actions_list, github_actions_status, github_actions_logs,
    github_releases, github_create_issue
]:
    tool_registry.register("github", tool)