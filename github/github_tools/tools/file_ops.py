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

# Register tools
tools = [stateful_search_files, remote_search]
for tool in tools:
    tool_registry.register("github", tool)

__all__ = ['stateful_search_files', 'remote_search']

