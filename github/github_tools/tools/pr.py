from kubiya_sdk.tools import Arg
from .base import GitHubCliTool
from kubiya_sdk.tools.models import FileSpec
from pathlib import Path

pr_create = GitHubCliTool(
    name="github_pr_create",
    description="Create a new pull request in a GitHub repository",
    content=f"""
#!/bin/bash
set -euo pipefail

# Install gettext for envsubst if not present
if ! command -v envsubst >/dev/null 2>&1; then
    apk add --quiet gettext > /dev/null 2>&1
fi

echo "🚀 Creating new pull request in $repo..."
echo "📝 Title: $title"
echo "📄 Base branch: $base"
echo "🔀 Head branch: $head"

# Get current user
GITHUB_ACTOR=$(gh api user --jq '.login')

# Create PR with proper quoting
PR_URL=$(gh pr create \
    --repo "$repo" \
    --title "$title" \
    --body "$body" \
    --base "$base" \
    --head "$head" \
    $([ -n "${{assignee:-}}" ] && echo "--assignee '$assignee'") \
    $([ -n "${{reviewer:-}}" ] && echo "--reviewer '$reviewer'"))

echo "✨ Pull request created successfully!"
echo "📋 Details: $PR_URL"
""",
    args=[
        Arg(name="repo", type="str", description="Repository name (owner/repo). Example: 'octocat/Hello-World'", required=True),
        Arg(name="title", type="str", description="Pull request title. Example: 'Add new feature: Dark mode'", required=True),
        Arg(name="body", type="str", description="Pull request description", required=True),
        Arg(name="base", type="str", description="The branch you want your changes pulled into. Example: 'main'", required=True),
        Arg(name="head", type="str", description="The branch that contains commits for your pull request. Example: 'feature/dark-mode'", required=True),
        Arg(name="assignee", type="str", description="The github user's login that this pr is to be assigned to. Use `@me` to self-assign", required=False),
        Arg(name="reviewer", type="str", description="The github user's login that should review this pr", required=False),
    ],
).register("github")

pr_list = GitHubCliTool(
    name="github_pr_list", 
    description="List pull requests in a GitHub repository.",
    content="""
echo "🔍 Searching for pull requests..."
if [ -n "$repo" ]; then
    echo "📁 Repository: https://github.com/$repo"
fi
if [ -n "$state" ]; then
    echo "📊 State: $state"
fi
if [ -n "$author" ]; then
    echo "👤 Author: https://github.com/$author"
fi
if [ -n "$assignee" ]; then
    echo "👥 Assignee: https://github.com/$assignee"
fi
if [ -n "$org" ]; then
    echo "🏢 Organization: https://github.com/$org"
fi

RESULT=$(gh search prs $([[ -n "$repo" ]] && echo "--repo $repo") $([[ -n "$state" ]] && echo "--state $state") $([[ -n "$limit" ]] && echo "--limit $limit") $([[ -n "$author" ]] && echo "--author $author") $([[ -n "$assignee" ]] && echo "--assignee $assignee") $([[ -n "$org" ]] && echo "--owner $org"))

echo "✨ Found pull requests:"
echo "$RESULT"
""",
    args=[
        Arg(name="repo", type="str", description="Repository name in 'owner/repo' format. Example: 'octocat/Hello-World'", required=False),
        Arg(name="state", type="str", description="Filter by pull request state (open, closed, merged, all). Example: 'open'", required=False),
        Arg(name="limit", type="str", description="Maximum number of pull requests to list. Example: 10", required=False),
        Arg(name="author", type="str", description="The github user's login of the pr's author. Example: joedoe. use `@me` to get prs authored by the user", required=False),
        Arg(name="assignee", type="str", description="The github user's login of the pr's assignee. Example: joe_doe.  use `@me` to get prs assigned to the user", required=False),
        Arg(name="org", type="str", description="The github organization to look for prs in. Example: octocat", required=False),
    ],
).register("github")

pr_view = GitHubCliTool(
    name="github_pr_view",
    description="View details of a specific pull request.",
    content="""
echo "🔍 Viewing pull request #$number in $repo..."
echo "📎 Link: https://github.com/$repo/pull/$number"
gh pr view --repo $repo $number
""",
    args=[
        Arg(name="repo", type="str", description="Repository name (owner/repo)", required=True),
        Arg(name="number", type="str", description="Pull request number. Example: 123", required=True),
    ],
).register("github")

pr_merge = GitHubCliTool(
    name="github_pr_merge",
    description="Merge a pull request.",
    content="""
echo "🔄 Attempting to merge pull request #$number in $repo..."
echo "📝 Using merge method: $merge_method"
echo "🔗 PR Link: https://github.com/$repo/pull/$number"

GITHUB_ACTOR=$(gh api user --jq '.login')
gh pr merge --repo $repo $number --$merge_method

echo "✅ Pull request merged successfully!"
""",
    args=[
        Arg(name="repo", type="str", description="Repository name in 'owner/repo' format. Example: 'octocat/Hello-World'", required=True),
        Arg(name="number", type="str", description="Pull request number. Example: 123", required=True),
        Arg(name="merge_method", type="str", description="Merge method to use (merge, squash, rebase). Example: 'squash'", required=True),
    ],
).register("github")

pr_close = GitHubCliTool(
    name="github_pr_close",
    description="Close a pull request without merging.",
    content="""
echo "🚫 Closing pull request #$number in $repo..."
echo "🔗 PR Link: https://github.com/$repo/pull/$number"
GITHUB_ACTOR=$(gh api user --jq '.login')
gh pr close --repo $repo $number
echo "✅ Pull request closed successfully!"
""",
    args=[
        Arg(name="repo", type="str", description="Repository name in 'owner/repo' format. Example: 'octocat/Hello-World'", required=True),
        Arg(name="number", type="str", description="Pull request number. Example: 123", required=True),
    ],
).register("github")

pr_comment = GitHubCliTool(
    name="github_pr_comment",
    description="Add a workflow failure analysis comment to a pull request with detailed error analysis and suggested fixes.",
    content="""
#!/bin/bash
set -euo pipefail

echo "💬 Processing comment for pull request #$number in $repo..."

# Validate JSON inputs
for input in "$workflow_steps" "$failures" "$fixes" "$run_details"; do
    if ! printf '%s' "$input" | jq empty; then
        echo "❌ Invalid JSON input provided"
        exit 1
    fi
done

# Get PR file changes
echo "📂 Fetching PR file changes..."
PR_FILES=$(gh api "repos/$repo/pulls/$number/files" --jq '[.[] | {
    filename: .filename,
    status: .status,
    additions: .additions,
    deletions: .deletions,
    changes: .changes,
    patch: .patch,
    previous_filename: .previous_filename
}]' 2>/dev/null) || {
    echo "❌ Failed to fetch PR files"
    exit 1
}

# Get PR details
echo "ℹ️ Fetching PR details..."
PR_DETAILS=$(gh api "repos/$repo/pulls/$number" --jq '{
    title: .title,
    description: .body,
    author: .user.login,
    created_at: .created_at,
    updated_at: .updated_at,
    changed_files: '"$PR_FILES"',
    commits_count: .commits,
    additions: .additions,
    deletions: .deletions,
    labels: [.labels[].name],
    base_branch: .base.ref,
    head_branch: .head.ref
}' 2>/dev/null) || {
    echo "❌ Failed to fetch PR details"
    exit 1
}

# Update run details with PR context
RUN_DETAILS=$(printf '%s' "$run_details" | jq '. + {pr_details: '"$PR_DETAILS"'}')

# Export variables for the Python script
export REPO="$repo"
export PR_NUMBER="$number"
export WORKFLOW_STEPS="$workflow_steps"
export FAILURES="$failures"
export FIXES="$fixes"
export ERROR_LOGS="$error_logs"
export RUN_DETAILS="$RUN_DETAILS"

# Generate comment using template
echo "🔨 Generating analysis comment..."
GENERATED_COMMENT=$(python3 /opt/scripts/comment_generator.py) || {
    echo "❌ Failed to generate comment"
    exit 1
}

# Get GitHub actor
GITHUB_ACTOR=$(gh api user --jq '.login') || {
    echo "❌ Failed to get GitHub user information"
    exit 1
}

# Get existing comments by the current user
echo "🔍 Checking for existing comments...!!!!!!!!!!!!"
EXISTING_COMMENT_ID=$(gh api "repos/$repo/issues/$number/comments" \
  --jq ".[] | select(.user.login == \"${GITHUB_ACTOR}\") | .id" \
  | sed -n 1p)


if [ -n "$EXISTING_COMMENT_ID" ]; then
    # Update existing comment
    echo "🔄 Updating existing comment..."
    
    # Get current comment content
    CURRENT_CONTENT=$(gh api "repos/$repo/issues/comments/$EXISTING_COMMENT_ID" --jq '.body')
    
    # Count existing edits
    EDIT_COUNT=$(printf '%s' "$CURRENT_CONTENT" | grep -c "Edit #" || echo "0")
    EDIT_COUNT=$((EDIT_COUNT + 1))
    
    # Create updated comment with edit history
    UPDATED_COMMENT="### Last Update (Edit #$EDIT_COUNT)

$GENERATED_COMMENT

---

*Note: To reduce noise, this comment was edited rather than creating a new one.*

<details><summary>Previous Comment</summary>

$CURRENT_CONTENT

</details>"

    # Update the comment
    if ! gh api "repos/$repo/issues/comments/$EXISTING_COMMENT_ID" \
        -X PATCH \
        -f body="$UPDATED_COMMENT"; then
        echo "❌ Failed to update comment"
        exit 1
    fi
    echo "✅ Comment updated successfully!"
else
    # Add new comment
    echo "➕ Adding new comment..."
    if ! gh pr comment --repo "$repo" "$number" --body "$GENERATED_COMMENT"; then
        echo "❌ Failed to add comment"
        exit 1
    fi
    echo "✅ Comment added successfully!"
fi
""",
    args=[
        Arg(
            name="repo", 
            type="str", 
            description="Repository name in 'owner/repo' format. Example: 'octocat/Hello-World'", 
            required=True
        ),
        Arg(
            name="number", 
            type="str", 
            description="Pull request number. Example: '123'", 
            required=True
        ),
        Arg(
            name="workflow_steps",
            type="str",
            description="""JSON array of workflow steps. Example:
[
    {
        "name": "Install Dependencies",
        "status": "success",
        "conclusion": "success",
        "number": 1
    }
]""",
            required=True
        ),
        Arg(
            name="failures",
            type="str",
            description="""JSON array of workflow failures. Example:
[
    {
        "step": "Run Tests",
        "error": "Test failed: expected 200 but got 404",
        "file": "tests/api_test.go",
        "line": "42"
    }
]""",
            required=True
        ),
        Arg(
            name="fixes",
            type="str",
            description="""JSON array of suggested fixes. Example:
[
    {
        "step": "Run Tests",
        "description": "Update the expected status code in the API test",
        "code_sample": "assert.Equal(t, http.StatusNotFound, response.StatusCode)"
    }
]""",
            required=True
        ),
        Arg(
            name="error_logs",
            type="str",
            description="Raw error logs from the workflow run",
            required=True
        ),
        Arg(
            name="run_details",
            type="str",
            description="""JSON object with workflow run details. Example:
{
    "id": "12345678",
    "name": "CI Pipeline",
    "started_at": "2024-01-20T10:00:00Z",
    "status": "completed",
    "conclusion": "failure",
    "actor": "octocat",
    "trigger_event": "pull_request"
}""",
            required=True
        ),
    ],
    with_files=[
        FileSpec(
            destination="/opt/scripts/comment_generator.py", 
            content=open(Path(__file__).parent.parent / 'scripts' / 'comment_generator.py').read()
        ),
        FileSpec(
            destination="/opt/scripts/templating/templates/workflow_failure.jinja2",
            content=open(Path(__file__).parent.parent / 'scripts' / 'templating' / 'templates' / 'workflow_failure.jinja2').read()
        ),
    ],
).register("github")

pr_review = GitHubCliTool(
    name="github_pr_review",
    description="Add a review to a pull request.",
    content="""
echo "👀 Adding review to pull request #$number in $repo..."
echo "📝 Review type: $review_type"
echo "🔗 PR Link: https://github.com/$repo/pull/$number"
GITHUB_ACTOR=$(gh api user --jq '.login')
gh pr review --repo $repo $number --$review_type $([[ -n "$body" ]] && echo "--body \\"$body\\"")
echo "✅ Review submitted successfully!"
""",
    args=[
        Arg(name="repo", type="str", description="Repository name in 'owner/repo' format. Example: 'octocat/Hello-World'", required=True),
        Arg(name="number", type="str", description="Pull request number. Example: 123", required=True),
        Arg(name="review_type", type="str", description="Type of review (approve, request-changes, comment). Example: 'approve'", required=True),
        Arg(name="body", type="str", description="Review comment. Example: 'LGTM! Approved with some minor suggestions.'", required=False),
    ],
).register("github")

pr_diff = GitHubCliTool(
    name="github_pr_diff",
    description="View the diff of a pull request.",
    content="""
echo "📊 Showing diff for pull request #$number in $repo..."
echo "🔗 PR Link: https://github.com/$repo/pull/$number"
gh pr diff --repo $repo $number
""",
    args=[
        Arg(name="repo", type="str", description="Repository name in 'owner/repo' format. Example: 'octocat/Hello-World'", required=True),
        Arg(name="number", type="str", description="Pull request number. Example: 123", required=True),
    ],
).register("github")

pr_ready = GitHubCliTool(
    name="github_pr_ready",
    description="Mark a pull request as ready for review.",
    content="""
echo "🎯 Marking pull request #$number in $repo as ready for review..."
echo "🔗 PR Link: https://github.com/$repo/pull/$number"
gh pr ready --repo $repo $number
echo "✅ Pull request is now ready for review!"
""",
    args=[
        Arg(name="repo", type="str", description="Repository name in 'owner/repo' format. Example: 'octocat/Hello-World'", required=True),
        Arg(name="number", type="str", description="Pull request number. Example: 123", required=True),
    ],
).register("github")

pr_checks = GitHubCliTool(
    name="github_pr_checks",
    description="View status checks for a pull request.",
    content="""
echo "🔍 Checking status for pull request #$number in $repo..."
echo "🔗 PR Link: https://github.com/$repo/pull/$number"
gh pr checks --repo $repo $number
""",
    args=[
        Arg(name="repo", type="str", description="Repository name in 'owner/repo' format. Example: 'octocat/Hello-World'", required=True),
        Arg(name="number", type="str", description="Pull request number. Example: 123", required=True),
    ],
).register("github")

pr_files = GitHubCliTool(
    name="github_pr_files",
    description="List files changed in a pull request.",
    content="""
echo "📁 Listing changed files for pull request #$number in $repo..."
echo "🔗 PR Link: https://github.com/$repo/pull/$number"
gh pr diff --repo $repo $number --name-only
""",
    args=[
        Arg(name="repo", type="str", description="Repository name in 'owner/repo' format. Example: 'octocat/Hello-World'", required=True),
        Arg(name="number", type="str", description="Pull request number. Example: 123", required=True),
    ],
).register("github")

pr_assign = GitHubCliTool(
    name="github_pr_assign",
    description="Assign a pull request to a github user",
    content="""
echo "👤 Assigning pull request #$number in $repo to $assignee..."
echo "🔗 PR Link: https://github.com/$repo/pull/$number"
echo "👥 Assignee Profile: https://github.com/$assignee"
gh pr edit --repo $repo $number --add-assignee $assignee
echo "✅ Pull request assigned successfully!"
""",
    args=[
        Arg(name="repo", type="str", description="Repository name in 'owner/repo' format. Example: 'octocat/Hello-World'", required=True),
        Arg(name="number", type="str", description="Pull request number. Example: 123", required=True),
        Arg(name="assignee", type="str", description="The github user's login to whom this pr is assigned to. Example: joe_doe. Use `@me` to self-assign", required=True),
    ],
).register("github")

pr_add_reviewer = GitHubCliTool(
    name="github_add_reviewer",
    description="Add a reviewer to a pull request",
    content="""
echo "👥 Adding reviewer $reviewer to pull request #$number in $repo..."
echo "🔗 PR Link: https://github.com/$repo/pull/$number"
echo "👤 Reviewer Profile: https://github.com/$reviewer"
gh pr edit --repo $repo $number --add-reviewer $reviewer
echo "✅ Reviewer added successfully!"
""",
    args=[
        Arg(name="repo", type="str", description="Repository name in 'owner/repo' format. Example: 'octocat/Hello-World'", required=True),
        Arg(name="number", type="str", description="Pull request number. Example: 123", required=True),
        Arg(name="reviewer", type="str", description="The github user's login that should be added as a reviewer to this pr. Example: joe_doe.", required=True),
    ],
).register("github")

# Export all PR tools
__all__ = ['pr_comment', 'pr_create', 'pr_review', 'pr_diff', 'pr_ready']
