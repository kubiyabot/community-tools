from kubiya_sdk.tools import Arg, Volume
from .base import GitHubCliTool
from kubiya_sdk.tools.registry import tool_registry

# Define the volume for git operations
GIT_VOLUME = Volume(
    name="gh_files",
    path="/opt/gh_files"
)

# Shell script for file operations
FILE_OPS_SCRIPT = '''
#!/bin/sh
set -e

# Function to search files
search_files() {
    local pattern="$1"
    local file_pattern="$2"
    local case_sensitive="$3"
    local show_content="$4"
    
    # Build grep options
    local grep_opts="-l"
    [ "$case_sensitive" != "true" ] && grep_opts="$grep_opts -i"
    
    # Track matches
    local total_matches=0
    
    echo "=== Search Results ==="
    
    if [ -n "$file_pattern" ]; then
        find . -type f -name "$file_pattern" -not -path "*/\\.*" | while read -r file; do
            if grep $grep_opts "$pattern" "$file" >/dev/null 2>&1; then
                total_matches=$((total_matches + 1))
                printf "✨ Match in: %s\\n" "${file#./}"
                
                if [ "$show_content" = "true" ]; then
                    printf " Content:\\n"
                    printf "-------------------\\n"
                    grep -n "$pattern" "$file" | while read -r line; do
                        printf "   %s\\n" "$line"
                    done
                    printf "-------------------\\n"
                fi
            fi
        done
    else
        git grep -n $grep_opts "$pattern" | while read -r line; do
            total_matches=$((total_matches + 1))
            printf "✨ %s\\n" "$line"
        done
    fi
    
    echo "=== Summary ==="
    if [ $total_matches -eq 0 ]; then
        echo "❌ No matches found"
    else
        printf "✅ Found %d matches\\n" "$total_matches"
    fi
}

# Function to perform remote search
remote_search() {
    local repo="$1"
    local pattern="$2"
    local page=1
    local per_page=100
    local total=0
    
    echo "=== Search Results ==="
    
    while true; do
        local results=$(gh api -X GET "search/code" \
            -f "q=repo:$repo $pattern" \
            -f "per_page=$per_page" \
            -f "page=$page" \
            --jq ".items[] | \\"📄 \\(.path)\\n   🔗 \\(.html_url)\\n   📝 \\(.text_matches[].fragment // \\"No preview\\")\\n\\"")
            
        [ -z "$results" ] && break
        
        echo "$results"
        total=$((total + $(echo "$results" | grep -c "^📄" || true)))
        page=$((page + 1))
    done
    
    echo "=== Summary ==="
    printf "✨ Found %d matches\\n" "$total"
}
'''

# Tool definitions using the shared script
stateful_search_files = GitHubCliTool(
    name="github_stateful_search_files",
    description="""Search for patterns in repository files.
    
WHEN TO USE:
- Need to find text patterns
- Want to search specific file types
- Need context around matches""",
    content=f'''
{FILE_OPS_SCRIPT}

setup_repo "${{repo}}" "${{branch}}"
search_files "${{pattern}}" "${{file_pattern}}" "${{case_sensitive}}" "${{show_content}}"
''',
    args=[
        Arg(name="repo", type="str", description="Repository name (owner/repo)", required=True),
        Arg(name="pattern", type="str", description="Pattern to search for", required=True),
        Arg(name="file_pattern", type="str", description="File pattern (e.g., '*.py')", required=False),
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
    content=f'''
{FILE_OPS_SCRIPT}

remote_search "${{repo}}" "${{pattern}}"
''',
    args=[
        Arg(name="repo", type="str", description="Repository name (owner/repo)", required=True),
        Arg(name="pattern", type="str", description="Search pattern", required=True),
    ]
)

# Add these file modification tools

stateful_modify_and_commit = GitHubCliTool(
    name="github_modify_and_commit",
    description="""Modify files and commit changes.
    
WHEN TO USE:
- Need to modify multiple files
- Want to commit changes
- Need to create/switch branches""",
    content=f'''
#!/bin/sh
set -e

echo "🔧 Setting up repository..."
setup_repo "${{repo}}" "${{branch}}"

echo "📝 Processing file modifications..."
for mod in $(echo "${{modifications}}" | jq -c '.[]'); do
    file=$(echo "$mod" | jq -r '.file')
    pattern=$(echo "$mod" | jq -r '.pattern')
    replacement=$(echo "$mod" | jq -r '.replacement')
    
    echo "✏️  Modifying: $file"
    if [ ! -f "$file" ]; then
        echo "❌ File not found: $file"
        continue
    fi
    
    # Create backup
    cp "$file" "$file.bak"
    
    # Perform replacement
    sed -i "s/$pattern/$replacement/g" "$file"
    
    # Show diff
    echo "📊 Changes for $file:"
    diff "$file.bak" "$file" || true
    rm "$file.bak"
done

if [ "${{create_branch}}" = "true" ]; then
    new_branch="${{branch_name:-feature/auto-update-$(date +%s)}}"
    echo "🌱 Creating new branch: $new_branch"
    git checkout -b "$new_branch"
fi

if [ -n "$(git status --porcelain)" ]; then
    echo "📦 Staging changes..."
    git add .
    
    echo "💾 Committing changes..."
    git commit -m "${{commit_message:-Auto-update: $(date)}}"
    
    echo "🚀 Pushing changes..."
    git push origin HEAD
    
    echo "✨ Changes pushed successfully"
else
    echo "ℹ️  No changes to commit"
fi
''',
    args=[
        Arg(name="repo", type="str", description="Repository name (owner/repo)", required=True),
        Arg(name="modifications", type="str", description='JSON array of modifications: [{"file": "path", "pattern": "old", "replacement": "new"}]', required=True),
        Arg(name="branch", type="str", description="Base branch to start from", required=False),
        Arg(name="create_branch", type="bool", description="Create new branch for changes", required=False),
        Arg(name="branch_name", type="str", description="Name for new branch (if creating)", required=False),
        Arg(name="commit_message", type="str", description="Custom commit message", required=False),
    ],
    with_volumes=[GIT_VOLUME]
)

stateful_create_pr = GitHubCliTool(
    name="github_create_pr",
    description="""Create pull request from changes.
    
WHEN TO USE:
- After modifying files
- Need to create PR
- Want to add reviewers""",
    content=f'''
#!/bin/sh
set -e

echo "🔍 Checking repository state..."
setup_repo "${{repo}}" "${{branch}}"

echo "📋 Creating pull request..."
PR_URL=$(gh pr create \
    --title "${{title}}" \
    --body "${{body}}" \
    --base "${{target_branch}}" \
    $([[ -n "${{reviewers}}" ]] && echo "--reviewer ${{reviewers}}") \
    $([[ -n "${{labels}}" ]] && echo "--label ${{labels}}"))

echo "✨ Pull request created successfully"
echo "🔗 URL: $PR_URL"
''',
    args=[
        Arg(name="repo", type="str", description="Repository name (owner/repo)", required=True),
        Arg(name="branch", type="str", description="Source branch with changes", required=True),
        Arg(name="target_branch", type="str", description="Target branch for PR", required=True),
        Arg(name="title", type="str", description="PR title", required=True),
        Arg(name="body", type="str", description="PR description", required=True),
        Arg(name="reviewers", type="str", description="Comma-separated list of reviewers", required=False),
        Arg(name="labels", type="str", description="Comma-separated list of labels", required=False),
    ],
    with_volumes=[GIT_VOLUME]
)

# Update the tools list
tools = [
    stateful_search_files,
    remote_search,
    stateful_modify_and_commit,
    stateful_create_pr
]

for tool in tools:
    tool_registry.register("github", tool)

__all__ = [
    'stateful_search_files',
    'remote_search',
    'stateful_modify_and_commit',
    'stateful_create_pr'
]

