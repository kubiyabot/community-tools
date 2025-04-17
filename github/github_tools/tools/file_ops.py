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

list_files = GitHubCliTool(
    name="github_list_files",
    description="List files in a GitHub repository with optional filtering using GitHub API",
    content="""
#!/bin/bash
set -euo pipefail

echo "📂 Listing files in repository: $repo"
[[ -n "$filter" ]] && echo "🔍 Filter: $filter"
[[ -n "$ref" ]] && echo "🔖 Ref: $ref"

# Build the API query
API_PATH="repos/$repo/git/trees/$([[ -n "$ref" ]] && echo "$ref" || echo "HEAD")?recursive=1"

# Fetch repository tree
echo "🔍 Fetching repository structure..."
TREE=$(gh api "$API_PATH")

# Process and display the tree structure
echo "$TREE" | jq -r '
    .tree | 
    sort_by(.path) | 
    .[] | 
    if .type == "tree" then
        "📁 " + .path + "/"
    else
        if .type == "blob" then
            "  📄 " + .path + 
            if env.show_details == "true" then
                "\\n    📊 Size: " + (.size|tostring) + " bytes"
            else 
                ""
            end
        else 
            empty 
        end
    end
' | while read -r line; do
    # Apply filters if specified
    if [ -n "$filter" ] && [[ ! "$line" =~ "$filter" ]]; then
        continue
    fi
    echo "$line"
done
echo "✨ File listing complete!"
""",
    args=[
        Arg(name="repo", type="str", description="Repository name (owner/repo). Example: 'octocat/Hello-World'", required=True),
        Arg(name="filter", type="str", description="Optional filter pattern for file names. Example: '.py' or 'test'", required=False),
        Arg(name="ref", type="str", description="Optional git reference (branch, tag, or commit SHA). Example: 'main' or 'v1.0.0'", required=False),
        Arg(name="show_details", type="bool", description="Show file size", required=False, default="false"),
    ],
)

# Update the tools list
tools = [
    get_file,
    remote_search,
    list_files
]

for tool in tools:
    tool_registry.register("github", tool)

__all__ = [
    'get_file',
    'remote_search',
    'stateful_create_pr',
    'list_files'
]

# Script for direct file content editing
FILE_EDIT_SCRIPT = '''
#!/bin/bash
set -euo pipefail

# Function to check if changes were made
check_changes() {
    if ! git diff --quiet "${file}"; then
        return 0  # Changes found
    else
        return 1  # No changes
    fi
}

# Setup workspace
WORKSPACE="/opt/gh_files/${KUBIYA_USER_EMAIL}/${repo}"
echo "🔧 Setting up workspace: ${WORKSPACE}"
rm -rf "${WORKSPACE}"
mkdir -p "${WORKSPACE}"
cd "${WORKSPACE}"

# Clone repo and setup
echo "🔄 Cloning repository..."
git clone "https://${GH_TOKEN}@github.com/${repo}.git" .

# Configure git
git config --global user.name "Kubiya Bot"
git config --global user.email "bot@kubiya.ai"

# Switch to or create branch
if [ -n "${branch_name}" ]; then
    echo "🌱 Creating branch: ${branch_name}"
    git fetch origin "${base_branch}"
    git checkout -b "${branch_name}" "origin/${base_branch}"
else
    echo "🔄 Checking out ${base_branch}"
    git checkout "${base_branch}"
fi

# Verify file exists or create new one
if [ ! -f "${file}" ]; then
    echo "📄 Creating new file: ${file}"
    mkdir -p "$(dirname "${file}")"
    touch "${file}"
fi

# Backup current content
cp "${file}" "${file}.bak"

# Write new content
echo "📝 Writing new content to: ${file}"
echo "${new_content}" > "${file}"

# Check if changes were made
if ! check_changes; then
    echo "⚠️  No changes were made to the file. New content is identical to existing content."
    rm "${file}.bak"
    exit 1
fi

# Show what changed
echo "📊 Changes made:"
git diff "${file}"

# Commit and push
echo "💾 Committing changes..."
git add "${file}"
git status --short
git commit -m "${commit_message}"

echo "🚀 Pushing changes..."
if [ -n "${branch_name}" ]; then
    git push -u origin "${branch_name}"
else
    git push origin "${base_branch}"
fi

# Verify push was successful
if git ls-remote --heads origin "${branch_name:-${base_branch}}" | grep -q "${branch_name:-${base_branch}}"; then
    echo "✨ Changes pushed successfully to ${branch_name:-${base_branch}}!"
    echo "🔗 Branch URL: https://github.com/${repo}/tree/${branch_name:-${base_branch}}"
else
    echo "❌ Failed to push changes!"
    exit 1
fi

# Cleanup
rm -rf "${WORKSPACE}"
'''

# Simplified edit file tool with direct content replacement
edit_file = GitHubCliTool(
    name="github_edit_file",
    description="Edit or create a file in a GitHub repository with new content",
    content=FILE_EDIT_SCRIPT,
    args=[
        Arg(name="repo", type="str", description="Repository name (owner/repo). Example: 'octocat/Hello-World'", required=True),
        Arg(name="file", type="str", description="Path to file to edit or create. Example: 'docs/README.md'", required=True),
        Arg(name="new_content", type="str", description="New content for the file", required=True),
        Arg(name="branch_name", type="str", description="New branch name (optional)", required=False),
        Arg(name="base_branch", type="str", description="Base branch name", required=False, default="main"),
        Arg(name="commit_message", type="str", description="Commit message", required=False, default="Update file"),
    ],
    with_volumes=[GIT_VOLUME]
)

# Register tool
tool_registry.register("github", edit_file)
__all__.append('edit_file')