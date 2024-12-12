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

list_files = GitHubCliTool(
    name="github_list_files",
    description="List files in a GitHub repository with optional filtering using GitHub API",
    content="""
echo "📂 Listing files in repository: $repo"
[[ -n "$path" ]] && echo "📁 Path: $path"
[[ -n "$filter" ]] && echo "🔍 Filter: $filter"
[[ -n "$ref" ]] && echo "🔖 Ref: $ref"

# Build the API query - get full tree in one request
API_PATH="repos/$repo/git/trees/$([[ -n "$ref" ]] && echo "$ref" || echo "HEAD")?recursive=1"

# Fetch repository tree
echo "🔍 Fetching repository structure..."
TREE=$(gh api "$API_PATH")

# Process and display the tree structure in a single jq command
echo "$TREE" | jq -r '
    .tree |
    # First sort everything by path
    sort_by(.path) |
    # Group by type and format output
    .[] |
    # Calculate depth for indentation
    . as $item |
    ($item.path | split("/") | length - 1) as $depth |
    # Create indentation string
    ($depth * 2) as $indent |
    # Format output based on type
    if $item.type == "tree" then
        ("📁 " + ($item.path | @sh | gsub("'\''"; ""))) + "/"
    else
        (
            # Create indentation
            (if $indent > 0 then (" " * $indent) else "" end) +
            # Add file emoji and path
            "📄 " + $item.path +
            # Add size if show_details is true
            if env.show_details == "true" then
                "\n" + (" " * ($indent + 3)) + "📊 Size: " + ($item.size | tostring) + " bytes" +
                "\n" + (" " * ($indent + 3)) + "🔒 SHA: " + $item.sha
            else "" end
        )
    end' | while read -r line; do
    # Apply filters if specified
    if [ -n "$path" ] && [[ ! "$line" =~ "$path" ]]; then
        continue
    fi
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
        Arg(name="path", type="str", description="Optional path to list files from. Example: 'src' or 'docs'", required=False),
        Arg(name="ref", type="str", description="Optional git reference (branch, tag, or commit SHA). Example: 'main' or 'v1.0.0'", required=False),
        Arg(name="show_details", type="bool", description="Show file size and SHA", required=False, default="false"),
    ],
)

# Update the tools list
tools = [
    get_file,
    remote_search,
    preview_modifications,
    stateful_modify_and_commit,
    stateful_create_pr,
    list_files
]

for tool in tools:
    tool_registry.register("github", tool)

__all__ = [
    'get_file',
    'remote_search',
    'preview_modifications',
    'stateful_modify_and_commit',
    'stateful_create_pr',
    'list_files'
]

# Simple script for file editing with sed
FILE_EDIT_SCRIPT = '''
#!/bin/bash
set -euo pipefail

# Configure git to use token authentication
setup_git_auth() {
    git config --global url."https://oauth2:${GH_TOKEN}@github.com/".insteadOf "https://github.com/"
}

# Edit file using sed
edit_file() {
    local file=$1
    local sed_statement=$2
    
    echo "📝 Editing file: $file"
    
    # Create backup
    cp "$file" "${file}.bak"
    
    # Apply sed command
    if [ "$(uname)" = "Darwin" ]; then
        sed -i '' "$sed_statement" "$file"
    else
        sed -i "$sed_statement" "$file"
    fi
    
    # Show diff
    echo "📊 Changes made:"
    diff "${file}.bak" "$file" || true
    rm "${file}.bak"
}
'''

# Simplified edit file tool
edit_file = GitHubCliTool(
    name="github_edit_file",
    description="Edit a file in a GitHub repository using sed",
    content=f'''
{FILE_EDIT_SCRIPT}

echo "🔄 Setting up repository: $repo"
setup_git_auth
gh repo clone "$repo" . || (cd . && git fetch)

# Create new branch if specified
if [ -n "$branch_name" ]; then
    echo "🌱 Creating branch: $branch_name"
    git checkout -b "$branch_name" origin/$base_branch
else
    git checkout "$base_branch"
fi

# Edit the file
edit_file "$file" "$sed_statement"

# Commit and push changes
git add "$file"
git commit -m "$commit_message"
git push origin HEAD

echo "✨ Changes pushed successfully!"

# Create PR if requested
if [ "$create_pr" = "true" ]; then
    echo "📝 Creating pull request..."
    PR_URL=$(gh pr create --title "$pr_title" --body "$pr_body" --base "$base_branch")
    echo "🔗 Pull request created: $PR_URL"
fi
''',
    args=[
        Arg(name="repo", type="str", description="Repository name (owner/repo). Example: 'octocat/Hello-World'", required=True),
        Arg(name="file", type="str", description="Path to file to edit. Example: 'README.md'", required=True),
        Arg(name="sed_statement", type="str", description="Sed command to apply. Example: 's/old/new/g'", required=True),
        Arg(name="base_branch", type="str", description="Base branch to work from", required=False, default="main"),
        Arg(name="branch_name", type="str", description="Optional new branch name", required=False),
        Arg(name="commit_message", type="str", description="Commit message", required=False, default="Update file"),
        Arg(name="create_pr", type="bool", description="Create PR after push", required=False, default="false"),
        Arg(name="pr_title", type="str", description="PR title (if creating PR)", required=False),
        Arg(name="pr_body", type="str", description="PR description (if creating PR)", required=False),
    ],
    with_volumes=[GIT_VOLUME]
)

# Update tools list and registry
tools.append(edit_file)
tool_registry.register("github", edit_file)
__all__.append('edit_file')
