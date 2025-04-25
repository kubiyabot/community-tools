from typing import List
from .base import ConfluenceTool, Arg
from kubiya_sdk.tools.registry import tool_registry

class ContentTools:
    """Confluence content access and management tools."""

    def __init__(self):
        """Initialize and register all Confluence content tools."""
        tools = [
            self.get_page_content(),
            self.search_content(),
            self.list_spaces(),
            self.get_space_content()
        ]
        
        for tool in tools:
            tool_registry.register("confluence", tool)

    def get_page_content(self) -> ConfluenceTool:
        """Retrieve content from a Confluence page."""
        return ConfluenceTool(
            name="confluence_page_content",
            description="Retrieve content from a Confluence page by ID or title and space",
            content="""
            # Install required packages silently
            apk add --no-cache --quiet jq curl bash ca-certificates
            
            # Create auth header with API token
            AUTH_HEADER="Authorization: Basic $(echo -n "$CONFLUENCE_USERNAME:$CONFLUENCE_API_TOKEN" | base64)"
            
            # Check if we have page_id or (title and space_key)
            if [ -z "$page_id" ] && ([ -z "$title" ] || [ -z "$space_key" ]); then
                echo "Error: Either page_id or both title and space_key are required"
                exit 1
            fi
            
            # Remove trailing slashes from URL
            CONFLUENCE_URL=$(echo "$CONFLUENCE_URL" | sed 's/\/$//')
            
            # If we have title and space_key but no page_id, search for the page
            if [ -z "$page_id" ] && [ -n "$title" ] && [ -n "$space_key" ]; then
                echo "Searching for page with title '$title' in space '$space_key'..."
                
                # For Atlassian Cloud
                if [[ "$CONFLUENCE_URL" == *"atlassian.net"* ]]; then
                    # Construct the API URL for v2 API
                    if [[ "$CONFLUENCE_URL" == */wiki ]]; then
                        SEARCH_URL="${CONFLUENCE_URL}/api/v2/pages?title=$title&space-key=$space_key&limit=1"
                    else
                        SEARCH_URL="$CONFLUENCE_URL/wiki/api/v2/pages?title=$title&space-key=$space_key&limit=1"
                    fi
                    
                    SEARCH_RESULT=$(curl -s -X GET "$SEARCH_URL" \
                        -H "$AUTH_HEADER" \
                        -H "Content-Type: application/json")
                    
                    # Check if we found any results
                    RESULT_COUNT=$(echo "$SEARCH_RESULT" | jq '.size // 0')
                    
                    if [ "$RESULT_COUNT" -eq 0 ]; then
                        echo "Error: No page found with title '$title' in space '$space_key'"
                        exit 1
                    fi
                    
                    # Extract the page ID from the search result
                    page_id=$(echo "$SEARCH_RESULT" | jq -r '.results[0].id')
                else
                    # For self-hosted Confluence
                    # URL encode the title for the CQL query
                    ENCODED_TITLE=$(echo "$title" | sed 's/ /%20/g')
                    SEARCH_QUERY="title%20~%20%22$ENCODED_TITLE%22%20AND%20space%20=%20$space_key"
                    
                    SEARCH_URL="$CONFLUENCE_URL/rest/api/content/search?cql=$SEARCH_QUERY&limit=1"
                    SEARCH_RESULT=$(curl -s -X GET "$SEARCH_URL" \
                        -H "$AUTH_HEADER" \
                        -H "Content-Type: application/json")
                    
                    # Check if we found any results
                    RESULT_COUNT=$(echo "$SEARCH_RESULT" | jq '.size // 0')
                    
                    if [ "$RESULT_COUNT" -eq 0 ]; then
                        echo "Error: No page found with title '$title' in space '$space_key'"
                        exit 1
                    fi
                    
                    # Extract the page ID from the search result
                    page_id=$(echo "$SEARCH_RESULT" | jq -r '.results[0].id')
                fi
                
                echo "Found page with ID: $page_id"
            fi

            # Now get the page content
            echo "Retrieving content for page ID: $page_id"
            
            # For Atlassian Cloud
            if [[ "$CONFLUENCE_URL" == *"atlassian.net"* ]]; then
                # Construct the API URL for v2 API
                if [[ "$CONFLUENCE_URL" == */wiki ]]; then
                    API_URL="${CONFLUENCE_URL}/api/v2/pages/$page_id?body-format=storage"
                else
                    API_URL="$CONFLUENCE_URL/wiki/api/v2/pages/$page_id?body-format=storage"
                fi
            else
                # For self-hosted Confluence
                API_URL="$CONFLUENCE_URL/rest/api/content/$page_id?expand=body.storage,space,history,metadata.labels"
            fi
            
            PAGE_DATA=$(curl -s -X GET "$API_URL" \
                -H "$AUTH_HEADER" \
                -H "Content-Type: application/json")

            # Check if we got a valid response
            if [[ "$CONFLUENCE_URL" == *"atlassian.net"* ]]; then
                # For Atlassian Cloud v2 API
                if [ "$(echo "$PAGE_DATA" | jq -r '.statusCode // ""')" = "404" ]; then
                    echo "Error: Page not found with ID: $page_id"
                    exit 1
                fi
                
                # Extract and display the page information
                TITLE=$(echo "$PAGE_DATA" | jq -r '.title // ""')
                SPACE_KEY=$(echo "$PAGE_DATA" | jq -r '.spaceId // ""')
                CREATED_DATE=$(echo "$PAGE_DATA" | jq -r '.createdAt // ""' | cut -d'T' -f1)
                CREATED_BY=$(echo "$PAGE_DATA" | jq -r '.authorId // ""')
                UPDATED_DATE=$(echo "$PAGE_DATA" | jq -r '.version.createdAt // ""' | cut -d'T' -f1)
                UPDATED_BY=$(echo "$PAGE_DATA" | jq -r '.version.authorId // ""')
                
                # Get labels if available
                LABELS=$(echo "$PAGE_DATA" | jq -r '.labels.results[] | .name' 2>/dev/null | tr '\n' ', ' | sed 's/,$//')
                if [ -z "$LABELS" ]; then
                    LABELS="None"
                fi
                
                # Extract the content
                CONTENT=$(echo "$PAGE_DATA" | jq -r '.body.storage.value // ""')
                
                # Display page metadata
                echo "=== Page Information ==="
                echo "Title: $TITLE"
                echo "Space: $SPACE_KEY"
                echo "Created: $CREATED_DATE by $CREATED_BY"
                echo "Updated: $UPDATED_DATE by $UPDATED_BY"
                echo "Labels: $LABELS"
                if [[ "$CONFLUENCE_URL" == */wiki ]]; then
                    echo "URL: $CONFLUENCE_URL/pages/$page_id"
                else
                    echo "URL: $CONFLUENCE_URL/wiki/pages/$page_id"
                fi
            else
                # For self-hosted Confluence
                if [ "$(echo "$PAGE_DATA" | jq -r '.statusCode // ""')" = "404" ]; then
                    echo "Error: Page not found with ID: $page_id"
                    exit 1
                fi
                
                # Extract and display the page information
                TITLE=$(echo "$PAGE_DATA" | jq -r '.title // ""')
                SPACE_NAME=$(echo "$PAGE_DATA" | jq -r '.space.name // ""')
                SPACE_KEY=$(echo "$PAGE_DATA" | jq -r '.space.key // ""')
                CREATED_DATE=$(echo "$PAGE_DATA" | jq -r '.history.createdDate // ""' | cut -d'T' -f1)
                CREATED_BY=$(echo "$PAGE_DATA" | jq -r '.history.createdBy.displayName // ""')
                UPDATED_DATE=$(echo "$PAGE_DATA" | jq -r '.history.lastUpdated.when // ""' | cut -d'T' -f1)
                UPDATED_BY=$(echo "$PAGE_DATA" | jq -r '.history.lastUpdated.by.displayName // ""')
                
                # Get labels if available
                LABELS=$(echo "$PAGE_DATA" | jq -r '.metadata.labels.results[] | .name' 2>/dev/null | tr '\n' ', ' | sed 's/,$//')
                if [ -z "$LABELS" ]; then
                    LABELS="None"
                fi
                
                # Extract the content
                CONTENT=$(echo "$PAGE_DATA" | jq -r '.body.storage.value // ""')
                
                # Display page metadata
                echo "=== Page Information ==="
                echo "Title: $TITLE"
                echo "Space: $SPACE_NAME ($SPACE_KEY)"
                echo "Created: $CREATED_DATE by $CREATED_BY"
                echo "Updated: $UPDATED_DATE by $UPDATED_BY"
                echo "Labels: $LABELS"
                echo "URL: $CONFLUENCE_URL/display/$SPACE_KEY/$page_id"
            fi
            
            # Display the content
            echo ""
            echo "=== Page Content ==="
            echo ""
            echo "$CONTENT"
            """,
            args=[
                Arg(name="page_id", description="ID of the Confluence page", required=False),
                Arg(name="title", description="Title of the Confluence page", required=False),
                Arg(name="space_key", description="Space key where the page is located", required=False)
            ],
            image="curlimages/curl:8.1.2"
        )

    def search_content(self) -> ConfluenceTool:
        """Search for content in Confluence."""
        return ConfluenceTool(
            name="confluence_search_content",
            description="Search for content in Confluence",
            content="""
            # Install required packages silently
            apk add --no-cache --quiet jq curl bash ca-certificates
            
            # Create auth header with API token
            AUTH_HEADER="Authorization: Basic $(echo -n "$CONFLUENCE_USERNAME:$CONFLUENCE_API_TOKEN" | base64)"
            
            if [ -z "$query" ]; then
                echo "Error: Search query is required"
                exit 1
            fi

            # Set limit with default
            LIMIT=${limit:-10}
            
            # Remove trailing slashes from URL
            CONFLUENCE_URL=$(echo "$CONFLUENCE_URL" | sed 's/\/$//')
            
            # For Atlassian Cloud
            if [[ "$CONFLUENCE_URL" == *"atlassian.net"* ]]; then
                # Construct the API URL for v2 API
                if [[ "$CONFLUENCE_URL" == */wiki ]]; then
                    SEARCH_URL="${CONFLUENCE_URL}/api/v2/pages?title=$query&limit=$LIMIT"
                    
                    # Add space key filter if provided
                    if [ -n "$space_key" ]; then
                        SEARCH_URL="$SEARCH_URL&space-key=$space_key"
                    fi
                else
                    SEARCH_URL="$CONFLUENCE_URL/wiki/api/v2/pages?title=$query&limit=$LIMIT"
                    
                    # Add space key filter if provided
                    if [ -n "$space_key" ]; then
                        SEARCH_URL="$SEARCH_URL&space-key=$space_key"
                    fi
                fi
            else
                # For self-hosted Confluence
                # URL encode the query for the CQL query
                ENCODED_QUERY=$(echo "$query" | sed 's/ /%20/g')
                SEARCH_QUERY="text%20~%20%22$ENCODED_QUERY%22"
                
                # Add space key filter if provided
                if [ -n "$space_key" ]; then
                    SEARCH_QUERY="$SEARCH_QUERY%20AND%20space%20=%20$space_key"
                fi
                
                SEARCH_URL="$CONFLUENCE_URL/rest/api/content/search?cql=$SEARCH_QUERY&limit=$LIMIT"
            fi
            
            echo "Searching for: $query"
            SEARCH_RESULT=$(curl -s -X GET "$SEARCH_URL" \
                -H "$AUTH_HEADER" \
                -H "Content-Type: application/json")
            
            # Check if we got a valid response
            if [[ "$CONFLUENCE_URL" == *"atlassian.net"* ]]; then
                # For Atlassian Cloud v2 API
                RESULT_COUNT=$(echo "$SEARCH_RESULT" | jq '.size // 0')
            else
                # For self-hosted Confluence
                RESULT_COUNT=$(echo "$SEARCH_RESULT" | jq '.size // 0')
            fi
            
            if [ "$RESULT_COUNT" -eq 0 ]; then
                echo "No results found for query: $query"
                exit 0
            fi
            
            echo "Found $RESULT_COUNT results:"
            echo ""
            
            # Display the results
            if [[ "$CONFLUENCE_URL" == *"atlassian.net"* ]]; then
                # For Atlassian Cloud v2 API
                if [[ "$CONFLUENCE_URL" == */wiki ]]; then
                    BASE_URL="$CONFLUENCE_URL/pages"
                else
                    BASE_URL="$CONFLUENCE_URL/wiki/pages"
                fi
                
                echo "$SEARCH_RESULT" | jq -r --arg base_url "$BASE_URL" '.results[] | "ID: \(.id)\nTitle: \(.title)\nSpace: \(.spaceId)\nURL: \($base_url)/\(.id)\n"'
            else
                # For self-hosted Confluence
                echo "$SEARCH_RESULT" | jq -r --arg base_url "$CONFLUENCE_URL" '.results[] | "ID: \(.id)\nTitle: \(.title)\nType: \(.type)\nSpace: \(.space.name) (\(.space.key))\nURL: \($base_url)/display/\(.space.key)/\(.id)\n"'
            fi
            """,
            args=[
                Arg(name="query", description="Search query", required=True),
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
            # Install required packages silently
            apk add --no-cache --quiet jq curl bash ca-certificates
            
            # Create auth header with API token
            AUTH_HEADER="Authorization: Basic $(echo -n "$CONFLUENCE_USERNAME:$CONFLUENCE_API_TOKEN" | base64)"
            
            # Set limit with default
            LIMIT=${limit:-25}
            
            # Remove trailing slashes from URL
            CONFLUENCE_URL=$(echo "$CONFLUENCE_URL" | sed 's/\/$//')
            
            # For Atlassian Cloud
            if [[ "$CONFLUENCE_URL" == *"atlassian.net"* ]]; then
                # Construct the API URL for v2 API
                if [[ "$CONFLUENCE_URL" == */wiki ]]; then
                    SPACES_URL="${CONFLUENCE_URL}/api/v2/spaces?limit=$LIMIT"
                else
                    SPACES_URL="$CONFLUENCE_URL/wiki/api/v2/spaces?limit=$LIMIT"
                fi
            else
                # For self-hosted Confluence
                SPACES_URL="$CONFLUENCE_URL/rest/api/space?limit=$LIMIT"
            fi
            
            echo "Retrieving list of Confluence spaces..."
            SPACES_RESULT=$(curl -s -X GET "$SPACES_URL" \
                -H "$AUTH_HEADER" \
                -H "Content-Type: application/json")
            
            # Check if we got any results
            RESULT_COUNT=$(echo "$SPACES_RESULT" | jq '.size // 0')
            
            if [ "$RESULT_COUNT" -eq 0 ]; then
                echo "No spaces found or you don't have access to any spaces."
                exit 0
            fi
            
            echo "Found $RESULT_COUNT spaces:"
            echo ""
            
            # Display the results
            if [[ "$CONFLUENCE_URL" == *"atlassian.net"* ]]; then
                # For Atlassian Cloud v2 API
                echo "$SPACES_RESULT" | jq -r '.results[] | "Key: \(.key)\nName: \(.name)\nType: \(.type)\nDescription: \(.description.plain.value // "No description")\n"'
            else
                # For self-hosted Confluence
                echo "$SPACES_RESULT" | jq -r --arg base_url "$CONFLUENCE_URL" '.results[] | "Key: \(.key)\nName: \(.name)\nType: \(.type)\nDescription: \(.description.plain.value // "No description")\nURL: \($base_url)/display/\(.key)\n"'
            fi
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
            # Install required packages silently
            apk add --no-cache --quiet jq curl bash ca-certificates
            
            # Create auth header with API token
            AUTH_HEADER="Authorization: Basic $(echo -n "$CONFLUENCE_USERNAME:$CONFLUENCE_API_TOKEN" | base64)"
            
            if [ -z "$space_key" ]; then
                echo "Error: Space key is required"
                exit 1
            fi

            # Set limit with default
            LIMIT=${limit:-25}
            
            # Remove trailing slashes from URL
            CONFLUENCE_URL=$(echo "$CONFLUENCE_URL" | sed 's/\/$//')
            
            # For Atlassian Cloud
            if [[ "$CONFLUENCE_URL" == *"atlassian.net"* ]]; then
                # Construct the API URL for v2 API
                if [[ "$CONFLUENCE_URL" == */wiki ]]; then
                    CONTENT_URL="${CONFLUENCE_URL}/api/v2/spaces/$space_key/pages?limit=$LIMIT"
                else
                    CONTENT_URL="$CONFLUENCE_URL/wiki/api/v2/spaces/$space_key/pages?limit=$LIMIT"
                fi
            else
                # For self-hosted Confluence
                CONTENT_URL="$CONFLUENCE_URL/rest/api/space/$space_key/content?limit=$LIMIT"
            fi
            
            echo "Retrieving content from space: $space_key"
            CONTENT_RESULT=$(curl -s -X GET "$CONTENT_URL" \
                -H "$AUTH_HEADER" \
                -H "Content-Type: application/json")
            
            # Check if we got a valid response
            if [ "$(echo "$CONTENT_RESULT" | jq -r '.statusCode // ""')" != "" ]; then
                echo "Error: $(echo "$CONTENT_RESULT" | jq -r '.message // "Unknown error"')"
                exit 1
            fi
            
            # Check if we got any results
            if [[ "$CONFLUENCE_URL" == *"atlassian.net"* ]]; then
                # For Atlassian Cloud v2 API
                RESULT_COUNT=$(echo "$CONTENT_RESULT" | jq '.size // 0')
                
                if [ "$RESULT_COUNT" -eq 0 ]; then
                    echo "No content found in space: $space_key"
                    exit 0
                fi
                
                # Display pages
                echo "=== Pages in $space_key ==="
                if [[ "$CONFLUENCE_URL" == */wiki ]]; then
                    BASE_URL="$CONFLUENCE_URL/pages"
                else
                    BASE_URL="$CONFLUENCE_URL/wiki/pages"
                fi
                
                echo "$CONTENT_RESULT" | jq -r --arg base_url "$BASE_URL" '.results[] | "ID: \(.id)\nTitle: \(.title)\nURL: \($base_url)/\(.id)\n"'
            else
                # For self-hosted Confluence
                PAGE_COUNT=$(echo "$CONTENT_RESULT" | jq '.page.size // 0')
                BLOG_COUNT=$(echo "$CONTENT_RESULT" | jq '.blogpost.size // 0')
                
                if [ "$PAGE_COUNT" -eq 0 ] && [ "$BLOG_COUNT" -eq 0 ]; then
                    echo "No content found in space: $space_key"
                    exit 0
                fi
                
                # Display pages
                if [ "$PAGE_COUNT" -gt 0 ]; then
                    echo "=== Pages in $space_key ==="
                    echo "$CONTENT_RESULT" | jq -r --arg base_url "$CONFLUENCE_URL" '.page.results[] | "ID: \(.id)\nTitle: \(.title)\nType: \(.type)\nURL: \($base_url)/display/'"$space_key"'/\(.id)\n"'
                fi
                
                # Display blog posts
                if [ "$BLOG_COUNT" -gt 0 ]; then
                    echo "=== Blog Posts in $space_key ==="
                    echo "$CONTENT_RESULT" | jq -r --arg base_url "$CONFLUENCE_URL" '.blogpost.results[] | "ID: \(.id)\nTitle: \(.title)\nType: \(.type)\nURL: \($base_url)/display/'"$space_key"'/\(.id)\n"'
                fi
            fi
            """,
            args=[
                Arg(name="space_key", description="Space key to get content from", required=True),
                Arg(name="limit", description="Maximum number of results to return", required=False)
            ],
            image="curlimages/curl:8.1.2"
        )

ContentTools() 