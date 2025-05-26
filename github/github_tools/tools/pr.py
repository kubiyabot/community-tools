from kubiya_sdk.tools import Arg
from .base import GitHubCliTool, GitHubRepolessCliTool
from kubiya_sdk.tools.registry import tool_registry
from kubiya_sdk.tools.models import FileSpec
from pathlib import Path


# Common disclaimer for automated actions
KUBIYA_DISCLAIMER = '''

---
> **Note**: This action was performed by Kubiya.ai on behalf of @${GITHUB_ACTOR}
> 
> 🤖 Automated action via [Kubiya.ai](https://kubiya.ai)
'''

# Default GitHub actor name to use when API call fails (app token case)
DEFAULT_GITHUB_ACTOR="kubiya-production[bot]"

# No shell functions here - all actor detection is inline in the shell scripts

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

# Try to get GitHub actor, properly handle errors
API_RESPONSE=$(gh api user 2>&1 || echo "ERROR")
if [[ "$API_RESPONSE" == *"Resource not accessible"* ]] || [[ "$API_RESPONSE" == *"ERROR"* ]]; then
    echo "Using default GitHub actor due to API error"
    GITHUB_ACTOR="kubiya-production"
else
    GITHUB_ACTOR=$(echo "$API_RESPONSE" | jq -r '.login' 2>/dev/null || echo "kubiya-production")
fi

# Get the expanded disclaimer
DISCLAIMER='{KUBIYA_DISCLAIMER}'
EXPANDED_DISCLAIMER=$(echo "$DISCLAIMER" | envsubst)

# Create full PR body with disclaimer
FULL_BODY="$body

$EXPANDED_DISCLAIMER"

# Create PR with proper quoting
PR_URL=$(gh pr create \
    --repo "$repo" \
    --title "$title" \
    --body "$FULL_BODY" \
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
)

pr_list = GitHubRepolessCliTool(
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
if [ -n "$org" ] && [ -z "$repo" ]; then
    echo "🏢 Organization: https://github.com/$org"
fi

# If both repo and org are provided, prioritize repo over org
if [ -n "$repo" ]; then
    RESULT=$(gh search prs --repo $repo $([[ -n "$state" ]] && echo "--state $state") $([[ -n "$limit" ]] && echo "--limit $limit") $([[ -n "$author" ]] && echo "--author $author") $([[ -n "$assignee" ]] && echo "--assignee $assignee"))
else
    RESULT=$(gh search prs $([[ -n "$state" ]] && echo "--state $state") $([[ -n "$limit" ]] && echo "--limit $limit") $([[ -n "$author" ]] && echo "--author $author") $([[ -n "$assignee" ]] && echo "--assignee $assignee") $([[ -n "$org" ]] && echo "--owner $org"))
fi

echo "✨ Found pull requests:"
echo "$RESULT"
""",
    args=[
        Arg(name="repo", type="str", description="Repository name in 'owner/repo' format. Example: 'octocat/Hello-World'", required=False),
        Arg(name="state", type="str", description="Filter by pull request state (open, closed, merged, all). Example: 'open'", required=False),
        Arg(name="limit", type="str", description="Maximum number of pull requests to list. Example: 10", required=False),
        Arg(name="author", type="str", description="The github user's login of the pr's author. Example: joedoe. use `@me` to get prs authored by the user", required=False),
        Arg(name="assignee", type="str", description="The github user's login of the pr's assignee. Example: joe_doe.  use `@me` to get prs assigned to the user", required=False),
        Arg(name="org", type="str", description="The github organization to look for prs in. Only used if repo is not specified. Example: octocat", required=False),
    ],
)

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
)

pr_merge = GitHubCliTool(
    name="github_pr_merge",
    description="Merge a pull request.",
    content="""
echo "🔄 Attempting to merge pull request #$number in $repo..."
echo "📝 Using merge method: $merge_method"
echo "🔗 PR Link: https://github.com/$repo/pull/$number"

# Try to get GitHub actor, properly handle errors
API_RESPONSE=$(gh api user 2>&1 || echo "ERROR")
if [[ "$API_RESPONSE" == *"Resource not accessible"* ]] || [[ "$API_RESPONSE" == *"ERROR"* ]]; then
    echo "Using default GitHub actor due to API error"
    GITHUB_ACTOR="kubiya-production"
else
    GITHUB_ACTOR=$(echo "$API_RESPONSE" | jq -r '.login' 2>/dev/null || echo "kubiya-production")
fi

gh pr merge --repo $repo $number --$merge_method -b "Merged via automated workflow${KUBIYA_DISCLAIMER}"

echo "✅ Pull request merged successfully!"
""",
    args=[
        Arg(name="repo", type="str", description="Repository name in 'owner/repo' format. Example: 'octocat/Hello-World'", required=True),
        Arg(name="number", type="str", description="Pull request number. Example: 123", required=True),
        Arg(name="merge_method", type="str", description="Merge method to use (merge, squash, rebase). Example: 'squash'", required=True),
    ],
)

pr_close = GitHubCliTool(
    name="github_pr_close",
    description="Close a pull request without merging.",
    content="""
echo "🚫 Closing pull request #$number in $repo..."
echo "🔗 PR Link: https://github.com/$repo/pull/$number"

# Try to get GitHub actor, properly handle errors
API_RESPONSE=$(gh api user 2>&1 || echo "ERROR")
if [[ "$API_RESPONSE" == *"Resource not accessible"* ]] || [[ "$API_RESPONSE" == *"ERROR"* ]]; then
    echo "Using default GitHub actor due to API error"
    GITHUB_ACTOR="kubiya-production"
else
    GITHUB_ACTOR=$(echo "$API_RESPONSE" | jq -r '.login' 2>/dev/null || echo "kubiya-production")
fi

gh pr close --repo $repo $number -c "Closed via automated workflow${KUBIYA_DISCLAIMER}"
echo "✅ Pull request closed successfully!"
""",
    args=[
        Arg(name="repo", type="str", description="Repository name in 'owner/repo' format. Example: 'octocat/Hello-World'", required=True),
        Arg(name="number", type="str", description="Pull request number. Example: 123", required=True),
    ],
)

pr_comment = GitHubCliTool(
    name="github_pr_comment",
    description="Add a comment to a pull request with proper formatting and timestamp.",
    content="""
# Format the timestamp in ISO format
TIMESTAMP=$(date -u +"%Y-%m-%d %H:%M:%S UTC")

# Create a formatted comment
echo "📝 Creating new comment..."
FORMATTED_COMMENT="### 💬 Comment Added via Kubiya AI

$body

---
<sub>🤖 This comment was generated automatically by Kubiya AI at $TIMESTAMP</sub>"

# Add the comment
COMMENT_URL=$(gh pr comment --repo $repo $number --body "$FORMATTED_COMMENT" 2>&1)
if [ $? -ne 0 ]; then
    echo "❌ Failed to add comment"
    echo "Error: $COMMENT_URL"
    exit 1
fi

echo "✅ Comment added successfully!"
echo "🔗 Comment URL: $COMMENT_URL"
echo "⏰ Timestamp: $TIMESTAMP"
""",
    args=[
        Arg(name="repo", type="str", description="Repository name in 'owner/repo' format. Example: 'octocat/Hello-World'", required=True),
        Arg(name="number", type="str", description="Pull request number. Example: 123", required=True),
        Arg(name="body", type="str", description="Comment text. Example: 'Great work! Just a few minor suggestions.'", required=True),
    ],
)

pr_comment_and_edit_if_exists = GitHubCliTool(
    name="github_pr_comment_and_edit_if_exists",
    description="Add a formatted comment to a pull request with proper formatting and timestamp. Updates existing comment if one exists.",
    content="""
# Format the timestamp in ISO format
TIMESTAMP=$(date -u +"%Y-%m-%d %H:%M:%S UTC")

# Create a formatted comment
echo "📝 Preparing comment..."
FORMATTED_COMMENT="### 💬 Comment Added via Kubiya AI

$body

---
<sub>🤖 This comment was generated automatically by Kubiya AI at $TIMESTAMP</sub>"

# Try to get GitHub actor, properly handle errors
API_RESPONSE=$(gh api user 2>&1 || echo "ERROR")
if [[ "$API_RESPONSE" == *"Resource not accessible"* ]] || [[ "$API_RESPONSE" == *"ERROR"* ]]; then
    echo "Using default GitHub actor due to API error"
    GITHUB_ACTOR="kubiya-production"
else
    GITHUB_ACTOR=$(echo "$API_RESPONSE" | jq -r '.login' 2>/dev/null || echo "kubiya-production")
fi

# Get existing comments by the current user
echo "🔍 Checking for existing comments..."
EXISTING_COMMENT_ID=$(gh api "repos/$repo/issues/$number/comments" \
  --jq '.[] | select(.user.login == "'"${GITHUB_ACTOR}"'" or (.body | contains("Kubiya"))) | .id' \
  | sed -n 1p)

if [ -n "$EXISTING_COMMENT_ID" ]; then
    # Update existing comment
    echo "🔄 Updating existing comment..."
    
    # Get current comment content
    CURRENT_CONTENT=$(gh api "repos/$repo/issues/comments/$EXISTING_COMMENT_ID" --jq '.body')
    
    # Create updated comment with edit history
    echo "🔨 Creating updated comment..."
    UPDATED_COMMENT="$FORMATTED_COMMENT

<details><summary>Previous Comment</summary>

$CURRENT_CONTENT

</details>"

    # Update the comment
    echo "🔨 Updating comment in $repo..."
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
    COMMENT_URL=$(gh pr comment --repo $repo $number --body "$FORMATTED_COMMENT" 2>&1)
    if [ $? -ne 0 ]; then
        echo "❌ Failed to add comment"
        echo "Error: $COMMENT_URL"
        exit 1
    fi
    COMMENT_ID=$(echo "$COMMENT_URL" | grep -o '[0-9]*$')

    # Verify the comment
    echo "🔍 Verifying comment..."
    COMMENT_CHECK=$(gh api repos/$repo/issues/comments/$COMMENT_ID)
    if [ $? -eq 0 ]; then
        echo "✅ Comment processed successfully for PR #$number"
        echo "🔗 Comment URL: $COMMENT_URL"
        echo "⏰ Timestamp: $TIMESTAMP"
    else
        echo "❌ Failed to verify comment"
        exit 1
    fi
fi
""",
    args=[
        Arg(name="repo", type="str", description="Repository name in 'owner/repo' format. Example: 'octocat/Hello-World'", required=True),
        Arg(name="number", type="str", description="Pull request number. Example: 123", required=True),
        Arg(name="body", type="str", description="Comment text. Example: 'Great work! Just a few minor suggestions.'", required=True),
    ],
)

github_pr_comment_workflow_failure = GitHubCliTool(
    name="github_pr_comment_workflow_failure",
    description="Add a workflow failure analysis comment to a pull request with detailed error analysis and suggested fixes. All text fields support GitHub Markdown formatting.",
    content="""
#!/bin/bash
set -euo pipefail

echo "💬 Processing comment for pull request #$number in $repo..."

# Export variables for the Python script
export REPO="$repo"
export PR_NUMBER="$number"
export WORKFLOW_FAILURE_SUMMARY="$failure_summary"
export WORKFLOW_FAILURE_REASON="$failure_cause"
export WORKFLOW_FAILURE_FIXES="$quick_fix_summary"
export RECOMMENDED_FIX="$detailed_fix_steps"
export DETAILED_ERROR_LOGS="$error_logs"

if ! command -v python3 >/dev/null 2>&1; then
    apk add --quiet python3 py3-pip >/dev/null 2>&1
fi

if ! command -v envsubst >/dev/null 2>&1; then
    apk add --quiet gettext >/dev/null 2>&1
fi

if ! python3 -c "import jinja2" >/dev/null 2>&1; then
    apk add py3-jinja2 >/dev/null 2>&1
fi

# Generate comment using template
echo "🔨 Generating analysis comment..."
GENERATED_COMMENT=$(python3 /opt/scripts/comment_generator.py 2>&1) || {
    echo "❌ Failed to generate comment: $GENERATED_COMMENT"
    exit 1
}

# Try to get GitHub actor, properly handle errors
API_RESPONSE=$(gh api user 2>&1 || echo "ERROR")
if [[ "$API_RESPONSE" == *"Resource not accessible"* ]] || [[ "$API_RESPONSE" == *"ERROR"* ]]; then
    echo "Using default GitHub actor due to API error"
    GITHUB_ACTOR="$DEFAULT_GITHUB_ACTOR"
else
    GITHUB_ACTOR=$(echo "$API_RESPONSE" | jq -r '.login' 2>/dev/null || echo "$DEFAULT_GITHUB_ACTOR")
fi

# Get existing comments by the current user
echo "🔍 Checking for existing comments..."
EXISTING_COMMENT_ID=$(gh api "repos/$repo/issues/$number/comments" \
  --jq '.[] | select(.user.login == "'"${GITHUB_ACTOR}"'" or (.body | contains("Kubiya"))) | .id' \
  | sed -n 1p)


if [ -n "$EXISTING_COMMENT_ID" ]; then
    # Update existing comment
    echo "🔄 Updating existing comment..."
    
    # Get current comment content
    CURRENT_CONTENT=$(gh api "repos/$repo/issues/comments/$EXISTING_COMMENT_ID" --jq '.body')
    
    # Create updated comment with edit history
    echo "🔨 Creating updated comment..."
    UPDATED_COMMENT="$GENERATED_COMMENT

<details><summary>Previous Comment</summary>

$CURRENT_CONTENT

</details>"

    # Update the comment
    echo "🔨 Updating comment in $repo..."
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
            name="failure_summary",
            type="str",
            description="A concise summary of what failed in the workflow. Supports GitHub Markdown formatting. Example: 'Build failed due to missing dependency'",
            required=True
        ),
        Arg(
            name="failure_cause",
            type="str",
            description="Explanation of why the workflow failed. Supports GitHub Markdown formatting. Example: 'The React package is missing from package.json'",
            required=True
        ),
        Arg(
            name="quick_fix_summary",
            type="str",
            description="Short summary of how to fix the issue. This appears in the main section of the comment. Supports GitHub Markdown formatting. Example: 'Add the missing React dependency to package.json'",
            required=True
        ),
        Arg(
            name="detailed_fix_steps",
            type="str",
            description="""Step-by-step fix instructions in a numbered list format. This should provide clear, specific actions to fix the issue.

Format as a numbered list with each step being a clear, actionable instruction. For example:

```markdown
1. Add the missing React dependency by running `npm install --save react`
2. Update the import statement in src/App.js from `import React from 'React'` to `import React from 'react'`
3. Rebuild the application with `npm run build` to verify the changes work

```

You can use GitHub Markdown formatting including:
- Code blocks with syntax highlighting
- Inline code with backticks
- Bold and italic text for emphasis
- Links to documentation

Keep each step concise and focused on a single action.
""",
            required=True
        ),
        Arg(
            name="error_logs",
            type="str",
            description="Raw error logs from the workflow run. Will be displayed in a code block. Example: 'Error: Cannot find module 'react'\n  at /app/src/index.js:1:1'",
            required=True
        )
    ],
    with_files=[
        FileSpec(
            destination="/opt/scripts/comment_generator.py", 
            content=open(Path(__file__).parent.parent / 'scripts' / 'comment_generator.py').read()
        ),
        FileSpec(
            destination="/opt/scripts/templates/workflow_failure.jinja2",
            content=open(Path(__file__).parent.parent / 'scripts' / 'templates' / 'workflow_failure.jinja2').read()
        ),
    ],
)


pr_review = GitHubCliTool(
    name="github_pr_review",
    description="Add a review to a pull request.",
    content="""
echo "👀 Adding review to pull request #$number in $repo..."
echo "📝 Review type: $review_type"
echo "🔗 PR Link: https://github.com/$repo/pull/$number"

# Try to get GitHub actor, properly handle errors
API_RESPONSE=$(gh api user 2>&1 || echo "ERROR")
if [[ "$API_RESPONSE" == *"Resource not accessible"* ]] || [[ "$API_RESPONSE" == *"ERROR"* ]]; then
    echo "Using default GitHub actor due to API error"
    GITHUB_ACTOR="kubiya-production"
else
    GITHUB_ACTOR=$(echo "$API_RESPONSE" | jq -r '.login' 2>/dev/null || echo "kubiya-production")
fi

FULL_BODY="$body${KUBIYA_DISCLAIMER}"
gh pr review --repo $repo $number --$review_type $([[ -n "$body" ]] && echo "--body \\"$FULL_BODY\\"")
echo "✅ Review submitted successfully!"
""",
    args=[
        Arg(name="repo", type="str", description="Repository name in 'owner/repo' format. Example: 'octocat/Hello-World'", required=True),
        Arg(name="number", type="str", description="Pull request number. Example: 123", required=True),
        Arg(name="review_type", type="str", description="Type of review (approve, request-changes, comment). Example: 'approve'", required=True),
        Arg(name="body", type="str", description="Review comment. Example: 'LGTM! Approved with some minor suggestions.'", required=False),
    ],
)

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
)

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
)

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
)

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
)

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
)

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
)

# Register all PR tools
for tool in [pr_create, pr_list, pr_view, pr_merge, pr_close, pr_comment, pr_comment_and_edit_if_exists, github_pr_comment_workflow_failure, pr_review, pr_diff, pr_ready, pr_checks, pr_files, pr_assign, pr_add_reviewer]:
    tool_registry.register("github", tool)

# Export all PR tools
__all__ = ['pr_create', 'pr_list', 'pr_view', 'pr_merge', 'pr_close', 'pr_comment', 'pr_comment_and_edit_if_exists', 'github_pr_comment_workflow_failure', 'pr_review', 'pr_diff', 'pr_ready', 'pr_checks', 'pr_files', 'pr_assign', 'pr_add_reviewer']
