from kubiya_sdk.tools import Arg
from .base import GitHubCliTool, GitHubRepolessCliTool
from kubiya_sdk.tools.registry import tool_registry

# Add collaborator to repository
add_collaborator = GitHubCliTool(
    name="github_add_collaborator",
    description="Add a collaborator to a GitHub repository with specified permission level",
    content="""
#!/bin/sh
set -e

echo "👥 Adding collaborator to repository..."
echo "📂 Repository: ${repo}"
echo "👤 Username: ${username}"
echo "🔑 Permission: ${permission:-write}"

# Check if user exists
if ! gh api users/${username} &>/dev/null; then
    echo "❌ User '${username}' not found on GitHub"
    exit 1
fi

# Add collaborator with specified permission
if gh api --method PUT "repos/${repo}/collaborators/${username}" \
    -f permission="${permission:-write}"; then
    echo "✅ Successfully added ${username} as a collaborator to ${repo} with ${permission:-write} permission"
else
    echo "❌ Failed to add collaborator"
    exit 1
fi

# Check if invitation is required
INVITE_STATUS=$(gh api "repos/${repo}/collaborators/${username}/permission" --jq '.user.login // "pending"')
if [ "$INVITE_STATUS" = "pending" ]; then
    echo "📧 Invitation sent to ${username}. They need to accept it to gain access."
    echo "🔗 They can accept at: https://github.com/${repo}/invitations"
fi
""",
    args=[
        Arg(name="repo", type="str", description="Repository name (owner/repo)", required=True),
        Arg(name="username", type="str", description="GitHub username to add as collaborator", required=True),
        Arg(name="permission", type="str", description="Permission level: 'pull' (read), 'push' (write), 'admin', 'maintain', or 'triage'", required=False, default="write"),
    ],
)

# Remove collaborator from repository
remove_collaborator = GitHubCliTool(
    name="github_remove_collaborator",
    description="Remove a collaborator from a GitHub repository",
    content="""
#!/bin/sh
set -e

echo "🗑️ Removing collaborator from repository..."
echo "📂 Repository: ${repo}"
echo "👤 Username: ${username}"

# Check if user is a collaborator
if ! gh api "repos/${repo}/collaborators/${username}" &>/dev/null; then
    echo "⚠️ User '${username}' is not a collaborator on ${repo}"
    exit 1
fi

# Remove collaborator
if gh api --method DELETE "repos/${repo}/collaborators/${username}"; then
    echo "✅ Successfully removed ${username} as a collaborator from ${repo}"
else
    echo "❌ Failed to remove collaborator"
    exit 1
fi
""",
    args=[
        Arg(name="repo", type="str", description="Repository name (owner/repo)", required=True),
        Arg(name="username", type="str", description="GitHub username to remove", required=True),
    ],
)

# List collaborators
list_collaborators = GitHubCliTool(
    name="github_list_collaborators",
    description="List all collaborators on a GitHub repository with their permission levels",
    content="""
#!/bin/sh
set -e

echo "👥 Listing collaborators for repository: ${repo}"
echo "🔍 Affiliation: ${affiliation:-all}"

# Get collaborators with permission details
COLLAB_DATA=$(gh api "repos/${repo}/collaborators?affiliation=${affiliation:-all}" --jq '[
    .[] | {
        username: .login,
        name: .name,
        type: .type,
        site_admin: .site_admin,
        permissions: .permissions,
        role_name: .role_name,
        url: .html_url
    }
]')

# Format output based on preference
if [ "${format}" = "json" ]; then
    echo "$COLLAB_DATA"
else
    echo "=== Repository Collaborators ==="
    echo "$COLLAB_DATA" | jq -r '.[] | 
        "👤 \(.username)" + 
        if .name then " (\(.name))" else "" end +
        if .type == "Bot" then " 🤖" else "" end +
        if .site_admin then " 🛡️" else "" end +
        "\\n   🔑 Role: \(.role_name // "Unknown")" +
        "\\n   🔗 Profile: \(.url)"
    '
    
    # Show summary
    TOTAL=$(echo "$COLLAB_DATA" | jq '. | length')
    ADMINS=$(echo "$COLLAB_DATA" | jq '[.[] | select(.permissions.admin == true)] | length')
    WRITE=$(echo "$COLLAB_DATA" | jq '[.[] | select(.permissions.push == true and .permissions.admin == false)] | length')
    READ=$(echo "$COLLAB_DATA" | jq '[.[] | select(.permissions.pull == true and .permissions.push == false and .permissions.admin == false)] | length')
    
    echo "\\n=== Summary ==="
    echo "📊 Total Collaborators: $TOTAL"
    echo "👑 Admin: $ADMINS"
    echo "✏️ Write: $WRITE"
    echo "👁️ Read-only: $READ"
fi
""",
    args=[
        Arg(name="repo", type="str", description="Repository name (owner/repo)", required=True),
        Arg(name="affiliation", type="str", description="Filter collaborators by affiliation: 'outside', 'direct', 'all'", required=False, default="all"),
        Arg(name="format", type="str", description="Output format: 'text' or 'json'", required=False, default="text"),
    ],
)

# Add team to repository
add_team = GitHubCliTool(
    name="github_add_team",
    description="Add a team to a GitHub repository with specified permission level",
    content="""
#!/bin/sh
set -e

echo "👥 Adding team to repository..."
echo "📂 Repository: ${repo}"
echo "👥 Team: ${team}"
echo "🔑 Permission: ${permission:-push}"

# Extract org from repo
ORG=$(echo "${repo}" | cut -d '/' -f 1)

# Validate team exists
if ! gh api "orgs/${ORG}/teams/${team}" &>/dev/null; then
    echo "❌ Team '${team}' not found in organization '${ORG}'"
    exit 1
fi

# Add team to repository
if gh api --method PUT "orgs/${ORG}/teams/${team}/repos/${repo}" \
    -f permission="${permission:-push}"; then
    echo "✅ Successfully added team '${team}' to ${repo} with ${permission:-push} permission"
else
    echo "❌ Failed to add team to repository"
    exit 1
fi
""",
    args=[
        Arg(name="repo", type="str", description="Repository name (owner/repo)", required=True),
        Arg(name="team", type="str", description="Team name or slug", required=True),
        Arg(name="permission", type="str", description="Permission level: 'pull' (read), 'push' (write), 'admin', 'maintain', or 'triage'", required=False, default="push"),
    ],
)

# Remove team from repository
remove_team = GitHubCliTool(
    name="github_remove_team",
    description="Remove a team from a GitHub repository",
    content="""
#!/bin/sh
set -e

echo "🗑️ Removing team from repository..."
echo "📂 Repository: ${repo}"
echo "👥 Team: ${team}"

# Extract org from repo
ORG=$(echo "${repo}" | cut -d '/' -f 1)

# Validate team exists
if ! gh api "orgs/${ORG}/teams/${team}" &>/dev/null; then
    echo "❌ Team '${team}' not found in organization '${ORG}'"
    exit 1
fi

# Remove team from repository
if gh api --method DELETE "orgs/${ORG}/teams/${team}/repos/${repo}"; then
    echo "✅ Successfully removed team '${team}' from ${repo}"
else
    echo "❌ Failed to remove team from repository"
    exit 1
fi
""",
    args=[
        Arg(name="repo", type="str", description="Repository name (owner/repo)", required=True),
        Arg(name="team", type="str", description="Team name or slug", required=True),
    ],
)

# List teams with access to repository
list_teams = GitHubCliTool(
    name="github_list_teams",
    description="List all teams with access to a GitHub repository",
    content="""
#!/bin/sh
set -e

echo "👥 Listing teams for repository: ${repo}"

# Get teams with permission details
TEAMS_DATA=$(gh api "repos/${repo}/teams" --jq '[
    .[] | {
        name: .name,
        slug: .slug,
        description: .description,
        permission: .permission,
        url: .html_url
    }
]')

# Format output based on preference
if [ "${format}" = "json" ]; then
    echo "$TEAMS_DATA"
else
    echo "=== Repository Teams ==="
    echo "$TEAMS_DATA" | jq -r '.[] | 
        "👥 \(.name) (\(.slug))\\n" +
        if .description then "   📝 \(.description)\\n" else "" end +
        "   🔑 Permission: \(.permission)\\n" +
        "   🔗 URL: \(.url)"
    '
    
    # Show summary
    TOTAL=$(echo "$TEAMS_DATA" | jq '. | length')
    ADMIN_TEAMS=$(echo "$TEAMS_DATA" | jq '[.[] | select(.permission == "admin")] | length')
    WRITE_TEAMS=$(echo "$TEAMS_DATA" | jq '[.[] | select(.permission == "push" or .permission == "write")] | length')
    READ_TEAMS=$(echo "$TEAMS_DATA" | jq '[.[] | select(.permission == "pull" or .permission == "read")] | length')
    
    echo "\\n=== Summary ==="
    echo "📊 Total Teams: $TOTAL"
    echo "👑 Admin: $ADMIN_TEAMS"
    echo "✏️ Write: $WRITE_TEAMS"
    echo "👁️ Read-only: $READ_TEAMS"
fi
""",
    args=[
        Arg(name="repo", type="str", description="Repository name (owner/repo)", required=True),
        Arg(name="format", type="str", description="Output format: 'text' or 'json'", required=False, default="text"),
    ],
)

# Set branch protection
set_branch_protection = GitHubCliTool(
    name="github_set_branch_protection",
    description="Set branch protection rules for a GitHub repository branch",
    content="""
#!/bin/sh
set -e

echo "🔒 Setting branch protection for: ${repo}/${branch}"

# Build protection rules JSON
PROTECTION_JSON='{
    "required_status_checks": null,
    "enforce_admins": false,
    "required_pull_request_reviews": null,
    "restrictions": null
}'

# Add required status checks if specified
if [ -n "${required_checks}" ]; then
    PROTECTION_JSON=$(echo "$PROTECTION_JSON" | jq --arg checks "$required_checks" '.required_status_checks = {
        "strict": true,
        "contexts": ($checks | split(","))
    }')
fi

# Add review requirements if specified
if [ "${require_reviews}" = "true" ]; then
    PROTECTION_JSON=$(echo "$PROTECTION_JSON" | jq --arg count "${required_approvals:-1}" '.required_pull_request_reviews = {
        "required_approving_review_count": ($count | tonumber),
        "dismiss_stale_reviews": true
    }')
fi

# Add admin enforcement if specified
if [ "${enforce_admins}" = "true" ]; then
    PROTECTION_JSON=$(echo "$PROTECTION_JSON" | jq '.enforce_admins = true')
fi

# Add push restrictions if specified
if [ -n "${restrict_pushes}" ]; then
    PROTECTION_JSON=$(echo "$PROTECTION_JSON" | jq --arg users "$restrict_pushes" '.restrictions = {
        "users": ($users | split(",")),
        "teams": []
    }')
fi

# Set branch protection
if gh api --method PUT "repos/${repo}/branches/${branch}/protection" -f "$(echo "$PROTECTION_JSON")"; then
    echo "✅ Successfully set branch protection rules for ${branch}"
else
    echo "❌ Failed to set branch protection"
    exit 1
fi

echo "🔒 Branch protection rules applied:"
echo "$PROTECTION_JSON" | jq '.'
""",
    args=[
        Arg(name="repo", type="str", description="Repository name (owner/repo)", required=True),
        Arg(name="branch", type="str", description="Branch name to protect", required=True),
        Arg(name="require_reviews", type="bool", description="Require pull request reviews before merging", required=False, default="false"),
        Arg(name="required_approvals", type="str", description="Number of required approving reviews", required=False, default="1"),
        Arg(name="required_checks", type="str", description="Comma-separated list of required status checks", required=False),
        Arg(name="enforce_admins", type="bool", description="Enforce restrictions for administrators", required=False, default="false"),
        Arg(name="restrict_pushes", type="str", description="Comma-separated list of usernames allowed to push", required=False),
    ],
)

# Get branch protection
get_branch_protection = GitHubCliTool(
    name="github_get_branch_protection",
    description="Get branch protection rules for a GitHub repository branch",
    content="""
#!/bin/sh
set -e

echo "🔍 Getting branch protection for: ${repo}/${branch}"

# Get branch protection
PROTECTION_DATA=$(gh api "repos/${repo}/branches/${branch}/protection" 2>/dev/null || echo '{"message": "Branch not protected"}')

# Check if branch is protected
if echo "$PROTECTION_DATA" | jq -e '.message' >/dev/null; then
    echo "⚠️ Branch '${branch}' is not protected"
    exit 0
fi

# Format output based on preference
if [ "${format}" = "json" ]; then
    echo "$PROTECTION_DATA"
else
    echo "=== Branch Protection Rules ==="
    
    # Status checks
    if echo "$PROTECTION_DATA" | jq -e '.required_status_checks' >/dev/null && [ "$(echo "$PROTECTION_DATA" | jq '.required_status_checks')" != "null" ]; then
        echo "✅ Required Status Checks:"
        echo "$PROTECTION_DATA" | jq -r '.required_status_checks | 
            "   🔒 Strict: \(.strict)",
            "   🔍 Contexts: \(.contexts | join(", "))"
        '
    else
        echo "❌ No required status checks"
    fi
    
    # PR reviews
    if echo "$PROTECTION_DATA" | jq -e '.required_pull_request_reviews' >/dev/null && [ "$(echo "$PROTECTION_DATA" | jq '.required_pull_request_reviews')" != "null" ]; then
        echo "👥 Required Pull Request Reviews:"
        echo "$PROTECTION_DATA" | jq -r '.required_pull_request_reviews | 
            "   👍 Required Approvals: \(.required_approving_review_count)",
            "   🧹 Dismiss Stale Reviews: \(.dismiss_stale_reviews)"
        '
    else
        echo "❌ No required pull request reviews"
    fi
    
    # Admin enforcement
    ENFORCE_ADMINS=$(echo "$PROTECTION_DATA" | jq -r '.enforce_admins.enabled')
    if [ "$ENFORCE_ADMINS" = "true" ]; then
        echo "👑 Enforce for Administrators: Yes"
    else
        echo "👑 Enforce for Administrators: No"
    fi
    
    # Push restrictions
    if echo "$PROTECTION_DATA" | jq -e '.restrictions' >/dev/null && [ "$(echo "$PROTECTION_DATA" | jq '.restrictions')" != "null" ]; then
        echo "🚫 Push Restrictions:"
        USERS=$(echo "$PROTECTION_DATA" | jq -r '.restrictions.users | map(.login) | join(", ")')
        TEAMS=$(echo "$PROTECTION_DATA" | jq -r '.restrictions.teams | map(.slug) | join(", ")')
        
        if [ -n "$USERS" ]; then
            echo "   👤 Users: $USERS"
        fi
        if [ -n "$TEAMS" ]; then
            echo "   👥 Teams: $TEAMS"
        fi
    else
        echo "🚫 No push restrictions"
    fi
fi
""",
    args=[
        Arg(name="repo", type="str", description="Repository name (owner/repo)", required=True),
        Arg(name="branch", type="str", description="Branch name", required=True),
        Arg(name="format", type="str", description="Output format: 'text' or 'json'", required=False, default="text"),
    ],
)

# Get user permission for repository
get_user_permission = GitHubCliTool(
    name="github_get_user_permission",
    description="Get a user's permission level for a GitHub repository",
    content="""
#!/bin/sh
set -e

echo "🔍 Checking permission for user: ${username} on ${repo}"

# Get user permission
PERMISSION_DATA=$(gh api "repos/${repo}/collaborators/${username}/permission" --jq '{
    user: .user.login,
    permission: .permission,
    role_name: .role_name
}')

# Format output based on preference
if [ "${format}" = "json" ]; then
    echo "$PERMISSION_DATA"
else
    echo "=== User Permission ==="
    echo "$PERMISSION_DATA" | jq -r '
        "👤 User: \(.user)",
        "🔑 Permission: \(.permission)",
        "👑 Role: \(.role_name)"
    '
    
    # Add human-readable explanation
    PERMISSION=$(echo "$PERMISSION_DATA" | jq -r '.permission')
    echo "\\n=== Explanation ==="
    case "$PERMISSION" in
        "admin")
            echo "✅ User has full administrative access to this repository"
            echo "   Can: manage settings, collaborators, webhooks, and delete repository"
            ;;
        "maintain")
            echo "✅ User has repository maintenance access"
            echo "   Can: manage issues, PRs, and some settings, but cannot delete repository"
            ;;
        "write" | "push")
            echo "✅ User has write access to this repository"
            echo "   Can: push to the repository, create branches, and open PRs"
            ;;
        "triage")
            echo "✅ User has triage access to this repository"
            echo "   Can: manage issues and PRs without write access"
            ;;
        "read" | "pull")
            echo "✅ User has read-only access to this repository"
            echo "   Can: view code, issues, and PRs, but cannot push changes"
            ;;
        *)
            echo "❌ User does not have access to this repository"
            ;;
    esac
fi
""",
    args=[
        Arg(name="repo", type="str", description="Repository name (owner/repo)", required=True),
        Arg(name="username", type="str", description="GitHub username to check", required=True),
        Arg(name="format", type="str", description="Output format: 'text' or 'json'", required=False, default="text"),
    ],
)

# Register all access management tools
ACCESS_TOOLS = [
    add_collaborator,
    remove_collaborator,
    list_collaborators,
    add_team,
    remove_team,
    list_teams,
    set_branch_protection,
    get_branch_protection,
    get_user_permission,
]

for tool in ACCESS_TOOLS:
    tool_registry.register("github", tool)

__all__ = [
    'add_collaborator', 'remove_collaborator', 'list_collaborators',
    'add_team', 'remove_team', 'list_teams',
    'set_branch_protection', 'get_branch_protection', 'get_user_permission'
] 