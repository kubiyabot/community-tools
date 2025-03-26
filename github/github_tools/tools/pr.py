from kubiya_sdk.tools import Arg
from .base import GitHubCliTool, GitHubRepolessCliTool
from kubiya_sdk.tools.registry import tool_registry

pr_create = GitHubCliTool(
    name="github_pr_create",
    description="Create a new pull request in a GitHub repository.",
    content="gh pr create --repo $repo --title \"$title\" --body \"$body\" --base $base --head $head $([[ -n \"$assignee\" ]] && echo \"--assignee $assignee\") $([[ -n \"$reviewer\" ]] && echo \"--reviewer $reviewer\")",
    args=[
        Arg(name="repo", type="str", description="Repository name in 'owner/repo' format. Example: 'octocat/Hello-World'", required=True),
        Arg(name="title", type="str", description="Pull request title. Example: 'Add new feature: Dark mode'", required=True),
        Arg(name="body", type="str", description="Pull request description. Example: 'This PR adds a dark mode feature to the app. It includes new styles and a toggle in the settings menu.'", required=True),
        Arg(name="base", type="str", description="The branch you want your changes pulled into. Example: 'main'", required=True),
        Arg(name="head", type="str", description="The branch that contains commits for your pull request. Example: 'feature/dark-mode'", required=True),
        Arg(name="assignee", type="str", description="The github user's login that this pr is to be assigned to. Example: joe_doe. Use `@me` to self-assign", required=False),
        Arg(name="reviewer", type="str", description="The github user's login that should review this pr. Example: joe_doe.", required=False),
    ],
)

pr_list = GitHubRepolessCliTool(
    name="github_pr_list",
    description="List pull requests in a GitHub repository.",
    content="gh search prs $([[ -n \"$repo\" ]] && echo \"--repo $repo\") $([[ -n \"$state\" ]] && echo \"--state $state\") $([[ -n \"$limit\" ]] && echo \"--limit $limit\") $([[ -n \"$author\" ]] && echo \"--author $author\") $([[ -n \"$assignee\" ]] && echo \"--assignee $assignee\") $([[ -n \"$org\" ]] && echo \"--owner $org\")",
    args=[
        Arg(name="repo", type="str", description="Repository name in 'owner/repo' format. Example: 'octocat/Hello-World'", required=False),
        Arg(name="state", type="str", description="Filter by pull request state (open, closed, merged, all). Example: 'open'", required=False),
        Arg(name="limit", type="int", description="Maximum number of pull requests to list. Example: 10", required=False),
        Arg(name="author", type="str", description="The github user's login of the pr's author. Example: joedoe. use `@me` to get prs authored by the user", required=False),
        Arg(name="assignee", type="str", description="The github user's login of the pr's assignee. Example: joe_doe.  use `@me` to get prs assigned to the user", required=False),
        Arg(name="org", type="str", description="The github organization to look for prs in. Example: octocat", required=False),
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
    description="Add a comment to a pull request with proper formatting and timestamp. Updates existing Kubiya comments if found.",
    content="""
# Format the timestamp in ISO format
TIMESTAMP=$(date -u +"%Y-%m-%d %H:%M:%S UTC")

# First, check for existing Kubiya comments
echo "🔍 Checking for existing Kubiya comments..."
EXISTING_COMMENT_ID=$(gh api "repos/$repo/issues/$number/comments" --jq ".[] | select(.user.login == \"@me\") | .id" | head -n 1)
echo "EXISTING_COMMENT_ID: $EXISTING_COMMENT_ID"

if [ -n "$EXISTING_COMMENT_ID" ]; then
    echo "Found existing Kubiya comment(s)"
    # Get the most recent comment ID
    COMMENT_ID=$(echo "$EXISTING_COMMENT_ID")
    # Get existing content
    EXISTING_BODY=$(gh api "repos/$repo/issues/$number/comments/$COMMENT_ID" --jq '.body')
    
    # Extract the previous content (everything between the header and the disclaimer)
    PREVIOUS_CONTENT=$(echo "$EXISTING_BODY" | awk '/### 💬 Comment Added via Kubiya AI/{p=1;next} /---/{p=0} p')
    
    # Prepare the updated comment with collapsible previous content
    FORMATTED_COMMENT="### 💬 Comment Added via Kubiya AI

$body

<details>
<summary>📜 Previous Comments</summary>

$PREVIOUS_CONTENT
</details>

---
<sub>🤖 This comment was generated automatically by Kubiya AI at $TIMESTAMP</sub>"

    # Create new comment instead of updating
    echo "📝 Creating new comment with history..."
    COMMENT_URL=$(gh pr comment --repo $repo $number --body "$FORMATTED_COMMENT" 2>&1)
    if [ $? -ne 0 ]; then
        echo "❌ Failed to add comment"
        echo "Error: $COMMENT_URL"
        exit 1
    fi
    COMMENT_ID=$(echo "$COMMENT_URL" | grep -o '[0-9]*$')
else
    # Create new comment if no existing Kubiya comment found
    echo "📝 Creating new comment..."
    FORMATTED_COMMENT="### 💬 Comment Added via Kubiya AI

$body

---
<sub>🤖 This comment was generated automatically by Kubiya AI at $TIMESTAMP</sub>"

    COMMENT_URL=$(gh pr comment --repo $repo $number --body "$FORMATTED_COMMENT" 2>&1)
    if [ $? -ne 0 ]; then
        echo "❌ Failed to add comment"
        echo "Error: $COMMENT_URL"
        exit 1
    fi
    COMMENT_ID=$(echo "$COMMENT_URL" | grep -o '[0-9]*$')
fi

# Verify the comment
echo "🔍 Verifying comment..."
COMMENT_CHECK=$(gh api repos/$repo/issues/comments/$COMMENT_ID)
if [ $? -eq 0 ]; then
    echo "✅ Comment processed successfully for PR #$number"
    echo "🔗 Comment URL: $COMMENT_URL"
    echo "⏰ Timestamp: $TIMESTAMP"
    
    # Verify content matches
    ACTUAL_BODY=$(echo "$COMMENT_CHECK" | jq -r .body)
    if [[ "$ACTUAL_BODY" == *"$body"* ]] && [[ "$ACTUAL_BODY" == *"$TIMESTAMP"* ]]; then
        echo "✅ Comment content verified"
    else
        echo "⚠️ Warning: Comment content may not match expected format"
    fi
else
    echo "❌ Failed to verify comment"
    exit 1
fi
""",
    args=[
        Arg(name="repo", type="str", description="Repository name in 'owner/repo' format. Example: 'octocat/Hello-World'", required=True),
        Arg(name="number", type="int", description="Pull request number. Example: 123", required=True),
        Arg(name="body", type="str", description="Comment text in markdown format. Example: '**Great work!** The changes look good.'", required=True),
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
    content="gh pr diff --repo $repo $number --name-only",
    args=[
        Arg(name="repo", type="str", description="Repository name in 'owner/repo' format. Example: 'octocat/Hello-World'", required=True),
        Arg(name="number", type="int", description="Pull request number. Example: 123", required=True),
    ],
)


pr_assign = GitHubCliTool(
    name="github_pr_assign",
    description="Assign a pull request to a github",
    content="gh pr edit --repo $repo $number --add-assignee $assignee",
    args=[
        Arg(name="repo", type="str", description="Repository name in 'owner/repo' format. Example: 'octocat/Hello-World'", required=True),
        Arg(name="number", type="int", description="Pull request number. Example: 123", required=True),
        Arg(name="assignee", type="str", description="The github user's login to whom this pr is assigned to. Example: joe_doe. Use `@me` to self-assign", required=True),
    ],
)


pr_add_reviewer = GitHubCliTool(
    name="github_add_reviewer",
    description="Add a reviewer to a pull request",
    content="gh pr edit --repo $repo $number --add-reviewer $reviewer",
    args=[
        Arg(name="repo", type="str", description="Repository name in 'owner/repo' format. Example: 'octocat/Hello-World'", required=True),
        Arg(name="number", type="int", description="Pull request number. Example: 123", required=True),
        Arg(name="reviewer", type="str", description="The github user's login that should be added as a reviewer to this pr. Example: joe_doe.", required=True),
    ],
)

# Register all PR tools
for tool in [pr_create, pr_list, pr_view, pr_merge, pr_close, pr_comment, pr_review, pr_diff, pr_ready, pr_checks, pr_files, pr_assign, pr_add_reviewer]:
    tool_registry.register("github", tool)

# Export all PR tools
__all__ = ['pr_create', 'pr_list', 'pr_view', 'pr_merge', 'pr_close', 'pr_comment', 'pr_review', 'pr_diff', 'pr_ready', 'pr_checks', 'pr_files', 'pr_assign', 'pr_add_reviewer']
