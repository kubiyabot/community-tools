# New file for search operations
from kubiya_workflow_sdk.tools import Arg
from .base import GitHubCliTool
from kubiya_workflow_sdk.tools.registry import tool_registry

github_search = GitHubCliTool(
    name="github_search",
    description="Search across GitHub repositories, code, issues, or pull requests",
    content="""
echo "🔍 Performing GitHub search..."
echo "🎯 Type: ${type}"
echo "🔎 Query: ${query}"
[[ -n "${limit}" ]] && echo "🔢 Limit: ${limit} results"
echo "📚 Advanced search: https://github.com/search/advanced"

if ! gh search "${type}" "${query}" $([ -n "${limit}" ] && echo "--limit ${limit}"); then
    echo "❌ Search failed. Common issues:"
    echo "  • Invalid search type (must be repos, code, issues, or prs)"
    echo "  • Invalid search syntax"
    echo "  • API rate limit exceeded"
    exit 1
fi

echo "✨ Search completed successfully!"
echo "🔗 View results on web: https://github.com/search?q=${query}&type=${type}"
""",
    args=[
        Arg(
            name="type",
            type="str",
            description="Type of search to perform. Examples: 'repos' (for repositories), 'code' (for code search), 'issues' (for issues), 'prs' (for pull requests)",
            required=True
        ),
        Arg(
            name="query",
            type="str",
            description='Search query to execute. Examples: "kubernetes in:name" (repos with kubernetes in name), "function language:python" (Python functions), "label:bug is:open" (open bug issues)',
            required=True
        ),
        Arg(
            name="limit",
            type="str",
            description="Maximum number of results to return. Example: 100 (default: 30)",
            required=False
        ),
    ],
)

code_search = GitHubCliTool(
    name="github_code_search",
    description="Search for code across repositories",
    content="""
echo "🔍 Searching for code..."
echo "🔎 Query: ${query}"
[[ -n "${language}" ]] && echo "💻 Language: ${language}"
[[ -n "${org}" ]] && echo "🏢 Organization: ${org}"

SEARCH_QUERY="${query}"
[[ -n "${language}" ]] && SEARCH_QUERY="$SEARCH_QUERY language:${language}"
[[ -n "${org}" ]] && SEARCH_QUERY="$SEARCH_QUERY org:${org}"

if ! gh search code "${SEARCH_QUERY}" --limit "${limit:-100}" --json path,repository,url --jq '.[] | "📄 \\(.path)\\n   📦 \\(.repository.nameWithOwner)\\n   🔗 \\(.url)\\n"'; then
    echo "❌ Search failed"
    exit 1
fi
""",
    args=[
        Arg(
            name="query",
            type="str",
            description='Code search query. Examples: "websocket connection", "def process_data", "import tensorflow"',
            required=True
        ),
        Arg(
            name="language",
            type="str",
            description='Programming language to filter by. Examples: "python", "javascript", "go", "java"',
            required=False
        ),
        Arg(
            name="org",
            type="str",
            description='Organization to search within. Examples: "kubernetes", "microsoft", "google"',
            required=False
        ),
        Arg(
            name="limit",
            type="str",
            description="Maximum number of results. Example: 50 (default: 100)",
            required=False
        ),
    ],
)

advanced_code_search = GitHubCliTool(
    name="github_advanced_code_search",
    description="Advanced code search with rich formatting and filtering",
    content="""
echo "🔍 Starting Advanced GitHub Code Search 🔮"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎯 Search Query: ${query}"
[[ -n "${language}" ]] && echo "🔤 Language: ${language}"
[[ -n "${org}" ]] && echo "🏢 Organization: ${org}"
[[ -n "${extension}" ]] && echo "📄 File Extension: ${extension}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Build search query
SEARCH_QUERY="${query}"
[[ -n "${language}" ]] && SEARCH_QUERY="$SEARCH_QUERY language:${language}"
[[ -n "${org}" ]] && SEARCH_QUERY="$SEARCH_QUERY org:${org}"
[[ -n "${extension}" ]] && SEARCH_QUERY="$SEARCH_QUERY extension:${extension}"
[[ -n "${path}" ]] && SEARCH_QUERY="$SEARCH_QUERY path:${path}"
[[ "${in_file}" == "true" ]] && SEARCH_QUERY="$SEARCH_QUERY in:file"
[[ "${in_path}" == "true" ]] && SEARCH_QUERY="$SEARCH_QUERY in:path"

echo "🔍 Final Search Query: $SEARCH_QUERY"
echo "🚀 Initiating search..."
echo

# Perform search with rich output
if ! RESULTS=$(gh search code "$SEARCH_QUERY" \
    --limit "${limit:-100}" \
    --json path,repository,url,content,matchCount \
    --jq '.[] | {
        path: .path,
        repo: .repository.nameWithOwner,
        url: .url,
        content: .content,
        matches: .matchCount,
        extension: (.path | split(".") | last),
        lines: (.content | split("\n") | length)
    }'); then
    echo "❌ Search failed"
    echo "💡 Tips:"
    echo "  • Check your search syntax"
    echo "  • Verify your access permissions"
    echo "  • Try reducing the scope of your search"
    exit 1
fi

# Format results based on output preference
case "${format}" in
    "json")
        echo "$RESULTS" | jq -c '.'
        ;;
    "markdown")
        echo "# 🔍 GitHub Code Search Results"
        echo
        echo "> 🎯 Query: \`$SEARCH_QUERY\`"
        echo
        echo "## 📊 Summary"
        echo
        TOTAL=$(echo "$RESULTS" | jq -s 'length')
        TOTAL_MATCHES=$(echo "$RESULTS" | jq -s '[.[].matches] | add')
        echo "📈 **Statistics**"
        echo "- 📁 Total files found: $TOTAL"
        echo "- 🎯 Total matches: $TOTAL_MATCHES"
        echo
        echo "## 📝 Results"
        echo
        echo "$RESULTS" | jq -r '
            "### 📄 [\(.path)](\(.url))\n" +
            "\n🏢 **Repository**: [\(.repo)](https://github.com/\(.repo))\n" +
            "📎 **Extension**: \(.extension)\n" +
            "📏 **Lines**: \(.lines)\n" +
            "🎯 **Matches**: \(.matches)\n\n" +
            "```\n\(.content)\n```\n" +
            "---\n"
        '
        ;;
    *)
        echo "🔍 Search Results Summary"
        echo "━━━━━━━━━━━━━━━━━━━━━━"
        TOTAL=$(echo "$RESULTS" | jq -s 'length')
        TOTAL_MATCHES=$(echo "$RESULTS" | jq -s '[.[].matches] | add')
        echo "📊 Quick Stats"
        echo "  📁 Files Found: $TOTAL"
        echo "  🎯 Total Matches: $TOTAL_MATCHES"
        echo
        
        # Show results with nice formatting
        echo "$RESULTS" | jq -r '
            "✨ Found Match ✨\n" +
            "📄 File: \(.path)\n" +
            "🏢 Repository: \(.repo)\n" +
            "📎 Extension: \(.extension)\n" +
            "📏 Lines: \(.lines)\n" +
            "🎯 Matches: \(.matches)\n" +
            "🔗 URL: \(.url)\n" +
            "\n📝 Content Preview:\n" +
            "━━━━━━━━━━━━━━━━━━━━━━\n" +
            (.content | split("\n") | map("  " + .) | join("\n")) +
            "\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
        '
        ;;
esac

# Add insights for larger result sets
if [ "$TOTAL" -gt 10 ]; then
    echo "✨ Search Insights ✨"
    echo "━━━━━━━━━━━━━━━━━"
    
    echo "📊 Top File Types:"
    echo "$RESULTS" | jq -s 'group_by(.extension) | map({extension: .[0].extension, count: length}) | sort_by(-.count)' | \
        jq -r '.[] | "  🔹 .\(.extension): \(.count) files"'
    
    echo
    echo "📊 Most Active Repositories:"
    echo "$RESULTS" | jq -s 'group_by(.repo) | map({repo: .[0].repo, count: length}) | sort_by(-.count)' | \
        jq -r '.[] | "  🔸 \(.repo): \(.count) files"'
    
    echo
    echo "💡 Search Tips:"
    echo "  • Use 'language:' to filter by programming language"
    echo "  • Add 'org:' to search within specific organizations"
    echo "  • Try 'extension:' to filter by file type"
    echo "  • Use quotes for exact phrase matching"
fi

echo
echo "✨ Search Complete! ✨"
""",
    args=[
        Arg(name="query", type="str", description="Search query", required=True),
        Arg(name="language", type="str", description="Filter by programming language", required=False),
        Arg(name="org", type="str", description="Filter by organization", required=False),
        Arg(name="extension", type="str", description="Filter by file extension", required=False),
        Arg(name="path", type="str", description="Filter by file path", required=False),
        Arg(name="in_file", type="bool", description="Search in file contents", required=False),
        Arg(name="in_path", type="bool", description="Search in file paths", required=False),
        Arg(name="format", type="str", description="Output format (text/json/markdown)", required=False, default="text"),
        Arg(name="limit", type="str", description="Maximum results to return", required=False, default="100"),
    ],
)

# Register tools
# tool_registry.register("github", github_search)
# tool_registry.register("github", code_search)
# tool_registry.register("github", advanced_code_search)