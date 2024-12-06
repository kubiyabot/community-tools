from kubiya_sdk.tools import Arg, Volume
from .base import GitHubCliTool
from kubiya_sdk.tools.registry import tool_registry

# Define the volume for git operations
GIT_VOLUME = Volume(
    name="gh_files",
    path="/opt/gh_files"
)

# Efficient repository management with user-specific state
REPO_MANAGEMENT = '''
get_user_hash() {
    if [ -z "$KUBIYA_USER_EMAIL" ]; then
        echo "❌ KUBIYA_USER_EMAIL environment variable is not set"
        exit 1
    fi
    echo "$KUBIYA_USER_EMAIL" | sha256sum | cut -d' ' -f1 | head -c 8
}

list_user_repos() {
    local org="$1"
    local page=1
    local per_page=30
    local total_repos=0
    
    echo "📚 Fetching repositories..."
    if [ -n "$org" ]; then
        echo "🏢 Organization: $org"
        while true; do
            local repos=$(gh api "orgs/$org/repos?page=$page&per_page=$per_page" --jq '.[] | {name: .name, visibility: .visibility, updated_at: .updated_at}')
            if [ -z "$repos" ]; then
                break
            fi
            echo "$repos"
            total_repos=$((total_repos + $(echo "$repos" | wc -l)))
            page=$((page + 1))
        done
    else
        echo "👤 User repositories"
        while true; do
            local repos=$(gh api "user/repos?page=$page&per_page=$per_page" --jq '.[] | {name: .name, visibility: .visibility, updated_at: .updated_at}')
            if [ -z "$repos" ]; then
                break
            fi
            echo "$repos"
            total_repos=$((total_repos + $(echo "$repos" | wc -l)))
            page=$((page + 1))
        done
    fi
    echo "📊 Total repositories: $total_repos"
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
    local base_dir="/opt/gh_files/$user_hash"
    [ ! -d "$base_dir" ] && return 0
    
    local cleaned=0
    echo "🧹 Checking for old states..."
    find "$base_dir" -mindepth 1 -maxdepth 1 -type d | while read dir; do
        if ! check_state_age "$dir"; then
            echo "   🗑️  Removing old state: $(basename "$dir")"
            rm -rf "$dir"
            cleaned=$((cleaned + 1))
        fi
    done
    [ $cleaned -gt 0 ] && echo "   ✨ Cleaned up $cleaned old states"
}

setup_repo() {
    local repo="$1"
    local branch="$2"
    
    # Get user-specific hash
    local user_hash=$(get_user_hash)
    
    # Create user and repo specific workspace
    WORK_DIR="/opt/gh_files/$user_hash/$(echo "$repo" | sed 's/[^a-zA-Z0-9]/_/g')"
    
    echo "👤 User workspace: $user_hash"
    echo "📦 Repository: $repo"
    
    # Get organization from repo
    local org=$(echo "$repo" | cut -d'/' -f1)
    echo "🏢 Organization: $org"
    
    # Show available repositories
    list_user_repos "$org"
    
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
                
                # Show some repo stats
                echo "📊 Repository stats:"
                echo "   📝 Latest commit: $(git log -1 --format='%h - %s')"
                echo "   👥 Contributors: $(git shortlog -sn --no-merges | wc -l)"
                
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

    # Show initial repo info
    echo "📊 Repository information:"
    echo "   📝 Default branch: $(git symbolic-ref refs/remotes/origin/HEAD | sed 's@^refs/remotes/origin/@@')"
    echo "   📚 Total branches: $(git branch -r | wc -l)"
    echo "   📦 Repository size: $(du -sh . | cut -f1)"

    # Handle branch
    if [ -n "$branch" ]; then
        echo "🔄 Switching to branch: $branch"
        if ! git checkout "$branch" 2>/dev/null; then
            if ! git checkout -b "$branch" "origin/$branch" 2>/dev/null; then
                echo "🌱 Creating new branch: $branch"
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
        echo "🧹 Cleaning up after error..."
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
    with_volumes=[GIT_VOLUME]
)

stateful_clone_repo = GitHubCliTool(
    name="github_stateful_clone_repo",
    description="""Clone and manage repository state.
    
WHEN TO USE:
- Need persistent local copy of repository
- Want to perform multiple operations
- Need branch management""",
    content=f'''
#!/bin/sh
set -e

{REPO_MANAGEMENT}

# Setup repository
setup_repo "${{repo}}" "${{branch}}"
echo "✅ Repository ready for operations"
''',
    args=[
        Arg(name="repo", type="str", description="Repository name (owner/repo)", required=True),
        Arg(name="branch", type="str", description="Branch to checkout", required=False),
    ],
    with_volumes=[GIT_VOLUME]
)

stateful_search_files = GitHubCliTool(
    name="github_stateful_search_files",
    description="""Search for patterns in repository files.
    
WHEN TO USE:
- Need to find text patterns
- Want to search specific file types
- Need context around matches""",
    content=f'''
#!/bin/sh
set -e

{REPO_MANAGEMENT}

setup_repo "${{repo}}" "${{branch}}"

echo "🔍 Searching for: ${{pattern}}"
[ -n "${{file_pattern}}" ] && echo "📁 In files matching: ${{file_pattern}}"

# Build search command
SEARCH_CMD="git grep -I -n" # -I ignores binary files, -n shows line numbers
[ "${{case_sensitive}}" != "true" ] && SEARCH_CMD="$SEARCH_CMD -i"
[ -n "${{context}}" ] && SEARCH_CMD="$SEARCH_CMD -C ${{context}}"

if [ -n "${{file_pattern}}" ]; then
    echo "=== 🔎 Search Results ==="
    find . -type f -name "${{file_pattern}}" -not -path "*/\.*" | while read -r file; do
        $SEARCH_CMD "${{pattern}}" "$file" 2>/dev/null || true
    done
else
    $SEARCH_CMD "${{pattern}}" 2>/dev/null || true
fi
''',
    args=[
        Arg(name="repo", type="str", description="Repository name (owner/repo)", required=True),
        Arg(name="pattern", type="str", description="Pattern to search for", required=True),
        Arg(name="file_pattern", type="str", description="File pattern (e.g., '*.py')", required=False),
        Arg(name="case_sensitive", type="bool", description="Case sensitive search", required=False),
        Arg(name="context", type="int", description="Lines of context around matches", required=False),
        Arg(name="branch", type="str", description="Branch to search in", required=False),
    ],
    with_volumes=[GIT_VOLUME]
)

stateful_recursive_search = GitHubCliTool(
    name="github_stateful_recursive_search",
    description="""Recursively search through repository with advanced filters.
    
WHEN TO USE:
- Need deep repository search
- Want to exclude certain paths
- Need complex pattern matching""",
    content=f'''
#!/bin/sh
set -e

{REPO_MANAGEMENT}

setup_repo "${{repo}}" "${{branch}}"

echo "🔍 Starting recursive search..."
echo "📝 Pattern: ${{pattern}}"

# Build find command
FIND_CMD="find . -type f"
[ -n "${{include_paths}}" ] && FIND_CMD="$FIND_CMD -path '${{include_paths}}'"
[ -n "${{exclude_paths}}" ] && FIND_CMD="$FIND_CMD ! -path '${{exclude_paths}}'"
[ -n "${{min_size}}" ] && FIND_CMD="$FIND_CMD -size +${{min_size}}"
[ -n "${{max_size}}" ] && FIND_CMD="$FIND_CMD -size -${{max_size}}"

# Build grep command
GREP_CMD="grep -l"
[ "${{case_sensitive}}" != "true" ] && GREP_CMD="$GREP_CMD -i"

echo "🔎 Searching..."
eval "$FIND_CMD" | while read -r file; do
    if $GREP_CMD "${{pattern}}" "$file" 2>/dev/null; then
        echo "✨ Found in: $file"
        if [ "${{show_content}}" = "true" ]; then
            echo "📄 Content:"
            grep -n --color=never "${{pattern}}" "$file"
            echo "---"
        fi
    fi
done
''',
    args=[
        Arg(name="repo", type="str", description="Repository name (owner/repo)", required=True),
        Arg(name="pattern", type="str", description="Search pattern", required=True),
        Arg(name="include_paths", type="str", description="Paths to include (e.g., './src/*')", required=False),
        Arg(name="exclude_paths", type="str", description="Paths to exclude (e.g., '*/test/*')", required=False),
        Arg(name="min_size", type="str", description="Minimum file size (e.g., '1M')", required=False),
        Arg(name="max_size", type="str", description="Maximum file size (e.g., '10M')", required=False),
        Arg(name="case_sensitive", type="bool", description="Case sensitive search", required=False),
        Arg(name="show_content", type="bool", description="Show matching content", required=False),
        Arg(name="branch", type="str", description="Branch to search in", required=False),
    ],
    with_volumes=[GIT_VOLUME]
)

remote_search = GitHubCliTool(
    name="github_remote_search",
    description="""Search repository content via GitHub API.
    
WHEN TO USE:
- Need quick search without cloning
- Want to search across branches
- Need to search large repositories""",
    content='''
#!/bin/sh
set -e

echo "🔍 Searching remotely in $repo..."
echo "📝 Query: $pattern"

page=1
per_page=100
total_results=0

while true; do
    results=$(gh api -X GET search/code \
        -f q="repo:$repo $pattern" \
        -f per_page=$per_page \
        -f page=$page \
        --jq '.items[] | {path: .path, url: .html_url}')
    
    if [ -z "$results" ]; then
        break
    fi
    
    echo "$results"
    count=$(echo "$results" | wc -l)
    total_results=$((total_results + count))
    page=$((page + 1))
done

echo "✨ Found $total_results matches"
''',
    args=[
        Arg(name="repo", type="str", description="Repository name (owner/repo)", required=True),
        Arg(name="pattern", type="str", description="Search pattern", required=True),
    ]
)

# Register tools
tools = [
    stateful_clone_repo,
    stateful_search_files,
    stateful_recursive_search,
    remote_search,
    stateful_modify_file,  # Keep existing tool
]

for tool in tools:
    tool_registry.register("github", tool)

__all__ = [
    'stateful_clone_repo',
    'stateful_search_files',
    'stateful_recursive_search',
    'remote_search',
    'stateful_modify_file',
]
