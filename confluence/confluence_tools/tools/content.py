from typing import List
import sys
from .base import ConfluenceTool, Arg
from kubiya_sdk.tools.registry import tool_registry

class ContentTools:
    """Confluence content access and management tools."""

    def __init__(self):
        """Initialize and register all Confluence content tools."""
        try:
            tools = [
                self.get_page_content(),
                self.search_content(),
                self.list_spaces(),
                self.get_space_content()
            ]
            
            for tool in tools:
                try:
                    tool_registry.register("confluence", tool)
                    print(f"✅ Registered: {tool.name}")
                except Exception as e:
                    print(f"❌ Failed to register {tool.name}: {str(e)}", file=sys.stderr)
                    raise
        except Exception as e:
            print(f"❌ Failed to register Confluence content tools: {str(e)}", file=sys.stderr)
            raise

    def get_page_content(self) -> ConfluenceTool:
        """Retrieve content from a Confluence page."""
        return ConfluenceTool(
            name="confluence_page_content",
            description="Retrieve content from a Confluence page by ID or title and space",
            content="""
            apk add --no-cache jq curl bash
            validate_confluence_connection

            # Check if we have page_id or (title and space_key)
            if [ -z "$page_id" ] && ([ -z "$title" ] || [ -z "$space_key" ]); then
                echo "Error: Either page_id or both title and space_key are required"
                exit 1
            fi

            # If we have title and space_key but no page_id, search for the page
            if [ -z "$page_id" ] && [ -n "$title" ] && [ -n "$space_key" ]; then
                echo "Searching for page with title '$title' in space '$space_key'..."
                
                # URL encode the title for the CQL query
                ENCODED_TITLE=$(echo "$title" | sed 's/ /%20/g')
                SEARCH_QUERY="title%20~%20%22$ENCODED_TITLE%22%20AND%20space%20=%20$space_key"
                
                SEARCH_RESULT=$(search_content "$SEARCH_QUERY" "1")
                
                # Check if we found any results
                RESULT_COUNT=$(echo "$SEARCH_RESULT" | jq '.size')
                
                if [ "$RESULT_COUNT" -eq 0 ]; then
                    echo "Error: No page found with title '$title' in space '$space_key'"
                    exit 1
                fi
                
                # Extract the page ID from the search result
                page_id=$(echo "$SEARCH_RESULT" | jq -r '.results[0].id')
                echo "Found page with ID: $page_id"
            fi

            # Now get the page content
            echo "Retrieving content for page ID: $page_id"
            PAGE_DATA=$(get_page_content "$page_id" "body.storage,metadata.labels")

            # Check if we got a valid response
            if [ "$(echo "$PAGE_DATA" | jq -r '.statusCode')" = "404" ]; then
                echo "Error: Page not found with ID: $page_id"
                exit 1
            fi

            # Extract and display the page information
            TITLE=$(echo "$PAGE_DATA" | jq -r '.title')
            SPACE_NAME=$(echo "$PAGE_DATA" | jq -r '.space.name')
            SPACE_KEY=$(echo "$PAGE_DATA" | jq -r '.space.key')
            CREATED_DATE=$(echo "$PAGE_DATA" | jq -r '.history.createdDate' | cut -d'T' -f1)
            CREATED_BY=$(echo "$PAGE_DATA" | jq -r '.history.createdBy.displayName')
            UPDATED_DATE=$(echo "$PAGE_DATA" | jq -r '.history.lastUpdated.when' | cut -d'T' -f1)
            UPDATED_BY=$(echo "$PAGE_DATA" | jq -r '.history.lastUpdated.by.displayName')
            
            # Get labels if available
            LABELS=$(echo "$PAGE_DATA" | jq -r '.metadata.labels.results[] | .name' 2>/dev/null | tr '\n' ', ' | sed 's/,$//')
            if [ -z "$LABELS" ]; then
                LABELS="None"
            fi
            
            # Extract the content
            CONTENT=$(echo "$PAGE_DATA" | jq -r '.body.storage.value')
            
            # Display page metadata
            echo "=== Page Information ==="
            echo "Title: $TITLE"
            echo "Space: $SPACE_NAME ($SPACE_KEY)"
            echo "Created: $CREATED_DATE by $CREATED_BY"
            echo "Updated: $UPDATED_DATE by $UPDATED_BY"
            echo "Labels: $LABELS"
            echo "URL: $CONFLUENCE_URL/display/$SPACE_KEY/$page_id"
            echo ""
            
            # Display content
            echo "=== Page Content ==="
            
            # Convert HTML to plain text (basic conversion)
            # Remove HTML tags, decode entities, etc.
            echo "$CONTENT" | sed 's/<[^>]*>//g' | sed 's/&nbsp;/ /g' | sed 's/&lt;/</g' | sed 's/&gt;/>/g' | sed 's/&amp;/\&/g'
            """,
            args=[
                Arg(name="page_id", description="ID of the Confluence page", required=False),
                Arg(name="title", description="Title of the Confluence page", required=False),
                Arg(name="space_key", description="Key of the Confluence space", required=False)
            ],
            image="curlimages/curl:8.1.2"
        )

    def search_content(self) -> ConfluenceTool:
        """Search for content in Confluence using CQL."""
        return ConfluenceTool(
            name="confluence_search",
            description="Search for content in Confluence using CQL (Confluence Query Language)",
            content="""
            apk add --no-cache jq curl bash
            validate_confluence_connection

            if [ -z "$query" ]; then
                echo "Error: Search query is required"
                exit 1
            fi

            # URL encode the query
            ENCODED_QUERY=$(echo "$query" | sed 's/ /%20/g')
            
            # Add space restriction if provided
            if [ -n "$space_key" ]; then
                ENCODED_QUERY="$ENCODED_QUERY%20AND%20space%20=%20$space_key"
            fi
            
            # Set limit with default
            LIMIT=${limit:-10}
            
            echo "Searching Confluence with query: $query"
            SEARCH_RESULT=$(search_content "$ENCODED_QUERY" "$LIMIT")
            
            # Check if we got any results
            RESULT_COUNT=$(echo "$SEARCH_RESULT" | jq '.size')
            
            if [ "$RESULT_COUNT" -eq 0 ]; then
                echo "No results found for query: $query"
                exit 0
            fi
            
            echo "Found $RESULT_COUNT results:"
            echo ""
            
            # Display the results
            echo "$SEARCH_RESULT" | jq -r '.results[] | "ID: \(.id)\nTitle: \(.title)\nType: \(.type)\nSpace: \(.space.name) (\(.space.key))\nURL: '"$CONFLUENCE_URL"'/display/\(.space.key)/\(.id)\n"'
            """,
            args=[
                Arg(name="query", description="CQL search query", required=True),
                Arg(name="space_key", description="Restrict search to this space key", required=False),
                Arg(name="limit", description="Maximum number of results to return", required=False)
            ],
            image="curlimages/curl:8.1.2"
        )

    def list_spaces(self) -> ConfluenceTool:
        """List available Confluence spaces."""
        return ConfluenceTool(
            name="confluence_list_spaces",
            description="List available Confluence spaces",
            content="""
            apk add --no-cache jq curl bash
            validate_confluence_connection

            # Set limit with default
            LIMIT=${limit:-25}
            
            echo "Retrieving list of Confluence spaces..."
            SPACES_RESULT=$(curl -s -X GET "$CONFLUENCE_URL/rest/api/space?limit=$LIMIT" \
                -H "$AUTH_HEADER" \
                -H "Content-Type: application/json")
            
            # Check if we got any results
            RESULT_COUNT=$(echo "$SPACES_RESULT" | jq '.size')
            
            if [ "$RESULT_COUNT" -eq 0 ]; then
                echo "No spaces found or you don't have access to any spaces."
                exit 0
            fi
            
            echo "Found $RESULT_COUNT spaces:"
            echo ""
            
            # Display the results
            echo "$SPACES_RESULT" | jq -r '.results[] | "Key: \(.key)\nName: \(.name)\nType: \(.type)\nDescription: \(.description.plain.value // "No description")\nURL: '"$CONFLUENCE_URL"'/display/\(.key)\n"'
            """,
            args=[
                Arg(name="limit", description="Maximum number of spaces to return", required=False)
            ],
            image="curlimages/curl:8.1.2"
        )

    def get_space_content(self) -> ConfluenceTool:
        """Get content from a Confluence space."""
        return ConfluenceTool(
            name="confluence_space_content",
            description="Get content from a Confluence space",
            content="""
            apk add --no-cache jq curl bash
            validate_confluence_connection

            if [ -z "$space_key" ]; then
                echo "Error: Space key is required"
                exit 1
            fi

            # Set limit with default
            LIMIT=${limit:-25}
            
            echo "Retrieving content from space: $space_key"
            CONTENT_RESULT=$(get_space_content "$space_key" "$LIMIT")
            
            # Check if we got a valid response
            if [ "$(echo "$CONTENT_RESULT" | jq -r '.statusCode // "200"')" != "200" ]; then
                echo "Error: $(echo "$CONTENT_RESULT" | jq -r '.message')"
                exit 1
            fi
            
            # Check if we got any results
            PAGE_COUNT=$(echo "$CONTENT_RESULT" | jq '.page.size')
            BLOG_COUNT=$(echo "$CONTENT_RESULT" | jq '.blogpost.size')
            
            if [ "$PAGE_COUNT" -eq 0 ] && [ "$BLOG_COUNT" -eq 0 ]; then
                echo "No content found in space: $space_key"
                exit 0
            fi
            
            # Display pages
            if [ "$PAGE_COUNT" -gt 0 ]; then
                echo "=== Pages in $space_key ==="
                echo "$CONTENT_RESULT" | jq -r '.page.results[] | "ID: \(.id)\nTitle: \(.title)\nURL: '"$CONFLUENCE_URL"'/display/\(.space.key)/\(.id)\n"'
            fi
            
            # Display blog posts
            if [ "$BLOG_COUNT" -gt 0 ]; then
                echo "=== Blog Posts in $space_key ==="
                echo "$CONTENT_RESULT" | jq -r '.blogpost.results[] | "ID: \(.id)\nTitle: \(.title)\nURL: '"$CONFLUENCE_URL"'/display/\(.space.key)/\(.id)\n"'
            fi
            """,
            args=[
                Arg(name="space_key", description="Key of the Confluence space", required=True),
                Arg(name="limit", description="Maximum number of content items to return", required=False)
            ],
            image="curlimages/curl:8.1.2"
        )

# Initialize tools
ContentTools() 