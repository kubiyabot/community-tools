from kubiya_sdk.tools import Arg
from .base import GitHubCliTool
from kubiya_sdk.tools.registry import tool_registry

# Efficient repository management with user-specific state
REPO_MANAGEMENT = '''
get_user_hash() {
    if [ -z "$KUBIYA_USER_EMAIL" ]; then
        echo "❌ KUBIYA_USER_EMAIL environment variable is not set"
        exit 1
    fi
    echo "$KUBIYA_USER_EMAIL" | sha256sum | cut -d' ' -f1 | head -c 8
}

check_state_age() {
    local dir="$1"
    local max_age=86400  # 24 hours in seconds
    
    if [ ! -f "$dir/.timestamp" ]; then
        return 1
    fi
    
    local age=$(($(date +%s) - $(cat "$dir/.timestamp")))
    [ $age -lt $max_age ]
    return $?
}

update_timestamp() {
    local dir="$1"
    date +%s > "$dir/.timestamp"
}

cleanup_old_states() {
    local user_hash=$(get_user_hash)
    local base_dir="/var/gh_files/$user_hash"
    [ ! -d "$base_dir" ] && return 0
    
    find "$base_dir" -mindepth 1 -maxdepth 1 -type d | while read dir; do
        if ! check_state_age "$dir"; then
            echo "🧹 Removing old state: $(basename "$dir")"
            rm -rf "$dir"
        fi
    done
}

setup_repo() {
    local repo="$1"
    local branch="$2"
    
    # Get user-specific hash
    local user_hash=$(get_user_hash)
    
    # Create user and repo specific workspace
    WORK_DIR="/opt/gh_files/$user_hash/$(echo "$repo" | sed 's/[^a-zA-Z0-9]/_/g')"
    
    echo "👤 User workspace: $user_hash"
    echo "📁 Repository: $repo"
    
    # Clean up old states first
    cleanup_old_states
    
    # Check if we can reuse existing state
    if [ -d "$WORK_DIR" ] && check_state_age "$WORK_DIR"; then
        echo "♻️  Reusing existing repository state"
        cd "$WORK_DIR"
        
        # Quick check if repo is in good state
        if git rev-parse --git-dir > /dev/null 2>&1; then
            # Verify remote matches
            local remote_url=$(git remote get-url origin)
            if [[ "$remote_url" == *"$repo"* ]]; then
                # Fetch latest changes
                echo "🔄 Updating repository..."
                git fetch origin
                
                # Check if working directory is clean
                if [ -z "$(git status --porcelain)" ]; then
                    # Reset to latest state
                    git reset --hard "origin/$branch"
                    update_timestamp "$WORK_DIR"
                    echo "✅ Repository state updated"
                    return 0
                fi
            else
                echo "⚠️  Repository mismatch, recreating state"
            fi
        fi
        
        echo "⚠️  Existing state unusable, recreating..."
    fi
    
    echo "🔧 Setting up fresh repository: $repo"
    rm -rf "$WORK_DIR"
    mkdir -p "$WORK_DIR"
    cd "$WORK_DIR"

    # Configure git
    git config --global user.email "$KUBIYA_USER_EMAIL"
    git config --global user.name "Kubiya Action"

    # Clone repo
    echo "📥 Cloning repository..."
    if ! gh repo clone "$repo" .; then
        echo "❌ Failed to clone repository"
        exit 1
    fi

    # Handle branch
    if [ -n "$branch" ]; then
        echo "🔄 Switching to branch: $branch"
        if ! git checkout "$branch" 2>/dev/null; then
            if ! git checkout -b "$branch" "origin/$branch" 2>/dev/null; then
                git checkout -b "$branch"
            fi
        fi
    fi

    update_timestamp "$WORK_DIR"
    echo "✅ Repository ready"
    return 0
}

cleanup_on_error() {
    if [ -d "$WORK_DIR" ]; then
        cd "$WORK_DIR"
        git reset --hard HEAD 2>/dev/null || rm -rf "$WORK_DIR"
    fi
}

trap cleanup_on_error ERR
'''

stateful_modify_file = GitHubCliTool(
    name="github_stateful_modify_file",
    description="""Modify file content with efficient state management.

WHEN TO USE:
- Need to modify a file in a repository
- Want to commit and push changes
- Need simple text replacement

FEATURES:
- Reuses existing clones when possible (< 24h old)
- Automatic cleanup of old states
- Fast operation with state caching
- Safe state management""",
    content=f'''
#!/bin/sh
set -e

{REPO_MANAGEMENT}

# Setup repository
setup_repo "${{repo}}" "${{branch}}"

if [ ! -f "${{file_path}}" ]; then
    echo "❌ File not found: ${{file_path}}"
    exit 1
fi

echo "✏️ Modifying file: ${{file_path}}"
cp "${{file_path}}" "${{file_path}}.bak"

# Perform replacement
sed -i "s/${{pattern}}/${{replacement}}/g" "${{file_path}}"

echo "📝 Changes made:"
diff "${{file_path}}.bak" "${{file_path}}" || true
rm "${{file_path}}.bak"

if [ "${{commit}}" = "true" ]; then
    git add "${{file_path}}"
    git commit -m "Update ${{file_path}}"
    if ! git push origin HEAD; then
        echo "⚠️  Push failed, trying to rebase..."
        git pull --rebase origin "${{branch}}"
        git push origin HEAD
    fi
    echo "✨ Changes pushed successfully"
fi
''',
    args=[
        Arg(name="repo", type="str", description="Repository name (owner/repo)", required=True),
        Arg(name="file_path", type="str", description="Path to file to modify", required=True),
        Arg(name="pattern", type="str", description="Text to replace", required=True),
        Arg(name="replacement", type="str", description="New text", required=True),
        Arg(name="branch", type="str", description="Branch to modify", required=False),
        Arg(name="commit", type="bool", description="Commit and push changes", required=False),
    ],
    with_volumes=["/opt/gh_files:/opt/gh_files"]
)

# Register tool
tool_registry.register("github", stateful_modify_file)
