from kubiya_sdk.tools import Arg
from .base import GitHubCliTool, GitHubRepolessCliTool
from kubiya_sdk.tools.registry import tool_registry

# Common disclaimer for automated actions
KUBIYA_DISCLAIMER = '''

---
> **Note**: This action was performed by Kubiya.ai on behalf of @${GITHUB_ACTOR}
> 
> 🤖 Automated action via [Kubiya.ai](https://kubiya.ai)
'''

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

GITHUB_ACTOR=$(gh api user --jq '.login')
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
GITHUB_ACTOR=$(gh api user --jq '.login')
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
    description="Add a comment to a pull request or update an existing comment with detailed workflow diagnostics.",
    content="""
#!/bin/bash

# Example Variables
repo="Kubiya-KubeCon/Kubiya-KubeCon"  # Replace with your GitHub repository
number="4"              # Pull request number to comment on
workflow_name="CI/CD Workflow"
workflow_steps="Step1,Step2,Step3"
failed_steps="Step1,Step3"
failures="Step1:Compile Error:Step3:Test Failure"
fixes="Step1:Fix the code style:Step3:Update the test cases"
error_logs="Compilation error in Step1.\nTests failed in Step3."
run_details="Workflow Run #42 on branch 'main'. Completed at 2024-12-18 14:30 UTC."
KUBIYA_DISCLAIMER="\n\n*Generated by Kubiya.ai*"

# Use echo instead of printf for better compatibility
echo "Processing comment for pull request #$number in $repo..."
echo "PR Link: https://github.com/$repo/pull/$number"
echo "Workflow Name: $workflow_name"
echo "Failures: $failures"
echo "Fixes: $fixes"
echo "Workflow Steps: $workflow_steps"
echo "Failed Steps: $failed_steps"
echo "Error Logs: $error_logs"
echo "Run Details: $run_details"

format_github_comment() {
    local workflow_name="$1"
    local failures="$2"
    local fixes="$3"
    local workflow_steps="$4"
    local failed_steps="$5"
    local error_logs="$6"
    local run_details="$7"

    # Generate the failures and reasons section
    local failure_details=""
    IFS=':'
    while read -r step reason rest; do
        if [ -n "$step" ] && [ -n "$reason" ]; then
            failure_details="${failure_details}- **${step}:** ${reason}\n"
        fi
    done < <(echo -e "${failures//:/$'\n'}")
    unset IFS

    # Generate the fixes section
    local fix_details=""
    IFS=':'
    while read -r step fix rest; do
        if [ -n "$step" ] && [ -n "$fix" ]; then
            fix_details="${fix_details}- **${step}:** ${fix}\n"
        fi
    done < <(echo -e "${fixes//:/$'\n'}")
    unset IFS

    # Generate mermaid diagram
    local mermaid_steps=""
    IFS=',' read -ra STEPS <<< "$workflow_steps"
    for step in "${STEPS[@]}"; do
        if [[ $failed_steps == *"$step"* ]]; then
            mermaid_steps="${mermaid_steps}    ${step}:::error --> "
        else
            mermaid_steps="${mermaid_steps}    ${step} --> "
        fi
    done
    mermaid_steps="${mermaid_steps% --> }" # Remove trailing arrow

    local mermaid_diagram="\\`\\`\\`mermaid\ngraph TD\n$mermaid_steps\n\nclassDef error fill:#ffcccc,stroke:#ff0000,stroke-width:4px;\n\\`\\`\\`"

    # Format error logs in a collapsible section
    local collapsible_logs="<details>\n  <summary>Error Logs</summary>\n\n\\`\\`\\`plaintext\n$error_logs\n\\`\\`\\`\n</details>"

    # Build the comment using more compatible string concatenation
    local comment="### Workflow Diagnostics\n\n"
    comment="${comment}#### What Failed?\n${failure_details}\n"
    comment="${comment}#### Suggested Fix\n${fix_details}\n"
    comment="${comment}#### Mermaid Diagram\n${mermaid_diagram}\n\n"
    comment="${comment}---\n\n### Logs and Details\n${collapsible_logs}\n\n"
    comment="${comment}---\n\n### Run Details\n${run_details}"
    
    echo -e "$comment"
}

# Get GitHub actor using gh CLI
GITHUB_ACTOR=$(gh api user --jq '.login')
FULL_COMMENT=$(format_github_comment "$workflow_name" "$failures" "$fixes" "$workflow_steps" "$failed_steps" "$error_logs" "$run_details")

# Add disclaimer
FULL_COMMENT="${FULL_COMMENT}${KUBIYA_DISCLAIMER}"

# Add new comment using gh CLI
echo "Adding new comment..."
gh pr comment --repo "$repo" "$number" --body "$FULL_COMMENT"
echo "Comment added successfully!"
""",
    args=[
        Arg(name="repo", type="str", description="Repository name in 'owner/repo' format. Example: 'octocat/Hello-World'", required=True),
        Arg(name="number", type="str", description="Pull request number. Example: 123", required=True),
        Arg(name="workflow_name", type="str", description="Name of the workflow being analyzed.", required=True),
        Arg(name="failures", type="str", description="Failures in the workflow steps, formatted as 'step:reason' pairs.", required=True),
        Arg(name="fixes", type="str", description="Fixes for the failures, formatted as 'step:fix' pairs.", required=True),
        Arg(name="workflow_steps", type="str", description="Comma-separated list of all workflow steps.", required=True),
        Arg(name="failed_steps", type="str", description="Comma-separated list of failed workflow steps.", required=True),
        Arg(name="error_logs", type="str", description="Error logs related to the workflow.", required=True),
        Arg(name="run_details", type="str", description="Details about the workflow run.", required=True),
    ],
)



pr_review = GitHubCliTool(
    name="github_pr_review",
    description="Add a review to a pull request.",
    content="""
echo "👀 Adding review to pull request #$number in $repo..."
echo "📝 Review type: $review_type"
echo "🔗 PR Link: https://github.com/$repo/pull/$number"
GITHUB_ACTOR=$(gh api user --jq '.login')
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
for tool in [pr_create, pr_list, pr_view, pr_merge, pr_close, pr_comment, pr_review, pr_diff, pr_ready, pr_checks, pr_files, pr_assign, pr_add_reviewer]:
    tool_registry.register("github", tool)

# Export all PR tools
__all__ = ['pr_create', 'pr_list', 'pr_view', 'pr_merge', 'pr_close', 'pr_comment', 'pr_review', 'pr_diff', 'pr_ready', 'pr_checks', 'pr_files', 'pr_assign', 'pr_add_reviewer']
