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

# Function to setup git repository
setup_repo() {
    local repo="$1"
    local branch="$2"
    
    # Clean working directory
    rm -rf ./*
    
    echo "🔄 Cloning repository..."
    gh repo clone "$repo" . || exit 1
    
    if [ -n "$branch" ]; then
        echo "🌱 Checking out branch: $branch"
        git checkout "$branch" || git checkout -b "$branch"
    fi
}

# Function to get file contents
get_file_contents() {
    local repo="$1"
    local file_path="$2"
    local ref="$3"

    echo "📄 Fetching file: $file_path"
    if [ -n "$ref" ]; then
        echo "📌 From ref: $ref"
        content=$(gh api "repos/$repo/contents/$file_path?ref=$ref" --jq '.content' | base64 -d)
    else
        content=$(gh api "repos/$repo/contents/$file_path" --jq '.content' | base64 -d)
    fi

    if [ -n "$content" ]; then
        echo "📝 File content:"
        echo "-------------------"
        echo "$content"
        echo "-------------------"
    else
        echo "❌ File not found or empty"
        exit 1
    fi
}

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
    local file="$3"
    local page=1
    local per_page=100
    local total=0
    
    echo "=== Search Results ==="

    if [ -n "$file" ]; then
        # Direct file content fetch
        echo "📄 Fetching specific file: $file"
        content=$(gh api "repos/$repo/contents/$file" --jq '.content' | base64 -d)
        if [ -n "$content" ]; then
            echo "📝 File content:"
            echo "-------------------"
            if [ -n "$pattern" ]; then
                echo "$content" | grep --color=always -n "$pattern" || echo "Pattern not found in file"
            else
                echo "$content"
            fi
            echo "-------------------"
            total=1
        else
            echo "❌ File not found or empty"
        fi
    else
        # Pattern search across repo
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
    fi
    
    echo "=== Summary ==="
    printf "✨ Found %d matches\\n" "$total"
}

# Function to preview changes before committing
preview_changes() {
    local modifications="$1"
    local create_branch="$2"
    local branch_name="$3"
    
    if [ "$create_branch" = "true" ]; then
        new_branch="${branch_name:-feature/auto-update-preview-$(date +%s)}"
        echo "🌱 Would create new branch: $new_branch"
    fi
    
    echo "📝 Previewing file modifications..."
    echo "$modifications" | jq -c '.[]' | while read -r mod; do
        file=$(echo "$mod" | jq -r '.file')
        pattern=$(echo "$mod" | jq -r '.pattern')
        replacement=$(echo "$mod" | jq -r '.replacement')
        
        echo "✏️  Would modify: $file"
        if [ ! -f "$file" ]; then
            echo "❌ File not found: $file"
            continue
        fi
        
        # Create temporary file for preview
        cp "$file" "$file.preview"
        sed -i "s/$pattern/$replacement/g" "$file.preview"
        
        # Show preview diff
        echo "📊 Preview of changes for $file:"
        diff --color "$file" "$file.preview" || true
        rm "$file.preview"
    done
}

# Function to modify files and commit changes
modify_and_commit() {
    local modifications="$1"
    local create_branch="$3"
    local branch_name="$4"
    local dry_run="$5"
    
    if [ "$dry_run" = "true" ]; then
        preview_changes "$modifications" "$create_branch" "$branch_name"
        return
    fi

    if [ "$create_branch" = "true" ]; then
        new_branch="${branch_name:-feature/auto-update-$(date +%s)}"
        echo "🌱 Creating new branch: $new_branch"
        git checkout -b "$new_branch"
    fi
    
    echo "📝 Processing file modifications..."
    echo "$modifications" | jq -c '.[]' | while read -r mod; do
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
    
    if [ -n "$(git status --porcelain)" ]; then
        echo "📦 Staging changes..."
        git add .
        
        echo "💾 Committing changes..."
        COMMIT_MSG="${commit_message:-Auto-update: $(date)}

$(add_disclaimer text)"
        
        git commit -m "$COMMIT_MSG"
        
        echo "🚀 Pushing changes..."
        git push origin HEAD
        
        echo "✨ Changes pushed successfully"
    else
        echo "ℹ️  No changes to commit"
    fi
}
'''

# Tool definitions using the shared script
get_file = GitHubCliTool(
    name="github_get_file",
    description="""Get contents of a specific file from a repository.
    
WHEN TO USE:
- Need to view file contents
- Want to fetch file from specific branch/ref""",
    content=f'''
{FILE_OPS_SCRIPT}

get_file_contents "${{repo}}" "${{file_path}}" "${{ref}}"
''',
    args=[
        Arg(name="repo", type="str", description="Repository name (owner/repo)", required=True),
        Arg(name="file_path", type="str", description="Path to file in repository", required=True),
        Arg(name="ref", type="str", description="Branch, tag, or commit SHA (optional)", required=False),
    ]
)

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
- Need to search large repositories
- Want to fetch specific file contents""",
    content=f'''
{FILE_OPS_SCRIPT}

remote_search "${{repo}}" "${{pattern}}" "${{file}}"
''',
    args=[
        Arg(name="repo", type="str", description="Repository name (owner/repo)", required=True),
        Arg(name="pattern", type="str", description="Search pattern (optional if fetching specific file)", required=False),
        Arg(name="file", type="str", description="Specific file path to fetch/search", required=False),
    ]
)

preview_modifications = GitHubCliTool(
    name="github_preview_modifications",
    description="""Preview file modifications without committing.
    
WHEN TO USE:
- Want to see changes before applying
- Need to validate modifications
- Want to check branch creation""",
    content=f'''
{FILE_OPS_SCRIPT}

setup_repo "${{repo}}" "${{branch}}"
preview_changes "${{modifications}}" "${{create_branch}}" "${{branch_name}}"
''',
    args=[
        Arg(name="repo", type="str", description="Repository name (owner/repo)", required=True),
        Arg(name="modifications", type="str", description='JSON array of modifications: [{"file": "path", "pattern": "old", "replacement": "new"}]', required=True),
        Arg(name="branch", type="str", description="Base branch to preview from", required=False),
        Arg(name="create_branch", type="bool", description="Preview branch creation", required=False),
        Arg(name="branch_name", type="str", description="Name for new branch", required=False),
    ],
    with_volumes=[GIT_VOLUME]
)

stateful_modify_and_commit = GitHubCliTool(
    name="github_modify_and_commit",
    description="Modify files and commit changes.",
    content=f'''
{FILE_OPS_SCRIPT}

setup_repo "${{repo}}" "${{branch}}"
modify_and_commit "${{modifications}}" "${{commit_message}}" "${{create_branch}}" "${{branch_name}}" "${{dry_run}}"
''',
    args=[
        Arg(name="repo", type="str", description="Repository name (owner/repo)", required=True),
        Arg(name="modifications", type="str", description='JSON array of modifications: [{"file": "path", "pattern": "old", "replacement": "new"}]', required=True),
        Arg(name="commit_message", type="str", description="Custom commit message", required=False),
        Arg(name="branch", type="str", description="Base branch to start from", required=False),
        Arg(name="create_branch", type="bool", description="Create new branch for changes", required=False),
        Arg(name="branch_name", type="str", description="Name for new branch (if creating)", required=False),
        Arg(name="dry_run", type="bool", description="Preview changes without committing", required=False),
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
{FILE_OPS_SCRIPT}

setup_repo "${{repo}}" "${{branch}}"

echo "📋 Creating pull request..."

# Add disclaimer to PR body
PR_BODY="${{body}}

$(add_disclaimer markdown)"

PR_URL=$(gh pr create \
    --title "${{title}}" \
    --body "$PR_BODY" \
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
    get_file,
    stateful_search_files,
    remote_search,
    preview_modifications,
    stateful_modify_and_commit,
    stateful_create_pr
]

for tool in tools:
    tool_registry.register("github", tool)

__all__ = [
    'get_file',
    'stateful_search_files',
    'remote_search',
    'preview_modifications',
    'stateful_modify_and_commit',
    'stateful_create_pr'
]
