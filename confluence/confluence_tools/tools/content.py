from typing import List
from .base import ConfluenceTool, Arg, FileSpec
from kubiya_sdk.tools.registry import tool_registry
import inspect
from .space_content_analyzer import space_content_analyzer

class ContentTools:
    """Confluence content access and management tools."""

    def __init__(self):
        """Initialize and register all Confluence content tools."""
        tools = [
            self.get_page_content(),
            self.search_content(),
            self.list_spaces(),
            self.get_space_content_analyzer(),
        ]
        
        for tool in tools:
            tool_registry.register("confluence", tool)

    def get_page_content(self) -> ConfluenceTool:
        """Retrieve content from a Confluence page."""
        return ConfluenceTool(
            name="confluence_page_content",
            description="Retrieve content from a Confluence page by ID or title and space, with optional label filtering",
            content="""
            # Install required packages silently
            apk add --no-cache --quiet jq curl bash ca-certificates >/dev/null 2>&1
            
            # Function to validate Confluence connection
            validate_confluence_connection() {
                if [ -z "$CONFLUENCE_URL" ] || [ -z "$CONFLUENCE_USERNAME" ] || [ -z "$CONFLUENCE_API_TOKEN" ]; then
                    echo "Error: Confluence credentials not properly configured. Please check CONFLUENCE_URL, CONFLUENCE_USERNAME, and CONFLUENCE_API_TOKEN."
                    exit 1
                fi
                
                # Test the connection
                TEST_URL="$CONFLUENCE_URL/rest/api/space?limit=1"
                TEST_RESULT=$(curl -s -X GET "$TEST_URL" \
                    -u "$CONFLUENCE_USERNAME:$CONFLUENCE_API_TOKEN" \
                    -H "Accept: application/json")
                
                # Check if the response is valid JSON
                if ! echo "$TEST_RESULT" | jq . >/dev/null 2>&1; then
                    echo "Error: Invalid response from Confluence API. Please check your credentials and URL."
                    echo "Response: $TEST_RESULT"
                    exit 1
                fi
                
                # Check for error messages in the response
                ERROR_MESSAGE=$(echo "$TEST_RESULT" | jq -r '.message // ""')
                if [ -n "$ERROR_MESSAGE" ]; then
                    echo "Error connecting to Confluence: $ERROR_MESSAGE"
                    exit 1
                fi
            }
            
            # Validate connection
            validate_confluence_connection
            
            # Check if we have page_id or (title and space_key) or label
            if [ -z "$page_id" ] && ([ -z "$title" ] || [ -z "$space_key" ]) && [ -z "$label" ]; then
                echo "Error: Either page_id, both title and space_key, or label are required"
                exit 1
            fi
            
            # Remove trailing slashes from URL
            CONFLUENCE_URL=$(echo "$CONFLUENCE_URL" | sed 's/\/$//')
            
            # If we have a label, search for pages with that label
            if [ -n "$label" ]; then
                # URL encode the label
                ENCODED_LABEL=$(echo "$label" | sed 's/ /%20/g')
                
                # Simple query for label
                SEARCH_QUERY="label%20=%20$ENCODED_LABEL"
                
                # Add space key filter if provided
                if [ -n "$space_key" ]; then
                    SEARCH_QUERY="$SEARCH_QUERY%20AND%20space%20=%20$space_key"
                fi
                
                # Set limit with default
                LIMIT=${limit:-50}
                
                SEARCH_URL="$CONFLUENCE_URL/rest/api/content/search?cql=$SEARCH_QUERY&limit=$LIMIT&expand=metadata.labels,space"
                
                echo "Searching for pages with label: $label"
                SEARCH_RESULT=$(curl -s -X GET "$SEARCH_URL" \
                    -u "$CONFLUENCE_USERNAME:$CONFLUENCE_API_TOKEN" \
                    -H "Accept: application/json")
                
                # Check if we got a valid response
                RESULT_COUNT=$(echo "$SEARCH_RESULT" | jq '.size // 0')
                
                if [ "$RESULT_COUNT" -eq 0 ]; then
                    echo "No pages found with label: $label"
                    exit 0
                fi
                
                # Check if the response is valid JSON before proceeding
                if ! echo "$SEARCH_RESULT" | jq . >/dev/null 2>&1; then
                    echo "Error: Invalid response from Confluence API when searching for label: $label"
                    echo "Response: $SEARCH_RESULT"
                    exit 1
                fi
                
                echo "Found $RESULT_COUNT pages with label '$label':"
                echo ""
                
                # Display the results in a simple format
                echo "$SEARCH_RESULT" | jq -r --arg base_url "$CONFLUENCE_URL" '.results[] | "Title: \(.title)\nID: \(.id)\nSpace: \(.space.name)\nURL: \($base_url)/pages/viewpage.action?pageId=\(.id)\n"'
                
                echo "Retrieving content for each page..."
                echo ""
                
                # Loop through each page and get its content
                for page_id in $(echo "$SEARCH_RESULT" | jq -r '.results[].id'); do
                    # Get the page content
                    API_URL="$CONFLUENCE_URL/rest/api/content/$page_id?expand=body.storage"
                    
                    PAGE_DATA=$(curl -s -X GET "$API_URL" \
                        -u "$CONFLUENCE_USERNAME:$CONFLUENCE_API_TOKEN" \
                        -H "Accept: application/json")
                    
                    # Check if the response is valid JSON before proceeding
                    if ! echo "$PAGE_DATA" | jq . >/dev/null 2>&1; then
                        echo "Error: Invalid response from Confluence API when retrieving page content"
                        echo "Response: $PAGE_DATA"
                        exit 1
                    fi
                    
                    # Extract the title
                    TITLE=$(echo "$PAGE_DATA" | jq -r '.title // ""')
                    
                    # Extract the content
                    CONTENT=$(echo "$PAGE_DATA" | jq -r '.body.storage.value // ""')
                    
                    # Output the title and content
                    echo "==============================================="
                    echo "# $TITLE"
                    echo "==============================================="
                    echo ""
                    
                    if [ -n "$CONTENT" ]; then
                        echo "$CONTENT"
                    else
                        echo "No content found or content is empty."
                    fi
                    
                    echo ""
                    echo ""
                done
                
                exit 0
            fi
            
            # If we have title and space_key but no page_id, search for the page
            if [ -z "$page_id" ] && [ -n "$title" ] && [ -n "$space_key" ]; then
                # For Atlassian Cloud
                if [[ "$CONFLUENCE_URL" == *"atlassian.net"* ]]; then
                    # Try the v1 API first as it seems to be working better
                    SEARCH_URL="$CONFLUENCE_URL/rest/api/content?type=page&spaceKey=$space_key&title=$title"
                    
                    SEARCH_RESULT=$(curl -s -X GET "$SEARCH_URL" \
                        -u "$CONFLUENCE_USERNAME:$CONFLUENCE_API_TOKEN" \
                        -H "Accept: application/json")
                    
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
                        -u "$CONFLUENCE_USERNAME:$CONFLUENCE_API_TOKEN" \
                        -H "Accept: application/json")
                    
                    # Check if we found any results
                    RESULT_COUNT=$(echo "$SEARCH_RESULT" | jq '.size // 0')
                    
                    if [ "$RESULT_COUNT" -eq 0 ]; then
                        echo "Error: No page found with title '$title' in space '$space_key'"
                        exit 1
                    fi
                    
                    # Extract the page ID from the search result
                    page_id=$(echo "$SEARCH_RESULT" | jq -r '.results[0].id')
                fi
            fi

            # Now get the page content
            # For Atlassian Cloud
            if [[ "$CONFLUENCE_URL" == *"atlassian.net"* ]]; then
                # Try the v1 API first as it seems to be working better
                API_URL="$CONFLUENCE_URL/rest/api/content/$page_id?expand=body.storage,space,history,metadata.labels"
            else
                # For self-hosted Confluence
                API_URL="$CONFLUENCE_URL/rest/api/content/$page_id?expand=body.storage,space,history,metadata.labels"
            fi
            
            PAGE_DATA=$(curl -s -X GET "$API_URL" \
                -u "$CONFLUENCE_USERNAME:$CONFLUENCE_API_TOKEN" \
                -H "Accept: application/json")
            
            # Check if the response is valid JSON before proceeding
            if ! echo "$PAGE_DATA" | jq . >/dev/null 2>&1; then
                echo "Error: Invalid response from Confluence API when retrieving page content"
                echo "Response: $PAGE_DATA"
                exit 1
            fi
            
            # Check if we got a valid response
            if [[ "$CONFLUENCE_URL" == *"atlassian.net"* ]]; then
                # For Atlassian Cloud v1 API
                if [ "$(echo "$PAGE_DATA" | jq -r '.statusCode // ""')" = "404" ]; then
                    echo "Error: Page not found with ID: $page_id"
                    exit 1
                fi
                
                # Extract the title
                TITLE=$(echo "$PAGE_DATA" | jq -r '.title // ""')
                
                # Extract the content - try different paths
                CONTENT=$(echo "$PAGE_DATA" | jq -r '.body.storage.value // .body.view.value // ""')
                
                # Output the title and content
                if [ -n "$TITLE" ]; then
                    echo "# $TITLE"
                    echo ""
                fi
                
                if [ -n "$CONTENT" ]; then
                    echo "$CONTENT"
                else
                    echo "No content found or content is empty."
                fi
            else
                # For self-hosted Confluence
                if [ "$(echo "$PAGE_DATA" | jq -r '.statusCode // ""')" = "404" ]; then
                    echo "Error: Page not found with ID: $page_id"
                    exit 1
                fi
                
                # Extract the title
                TITLE=$(echo "$PAGE_DATA" | jq -r '.title // ""')
                
                # Extract the content
                CONTENT=$(echo "$PAGE_DATA" | jq -r '.body.storage.value // ""')
                
                # Output the title and content
                if [ -n "$TITLE" ]; then
                    echo "# $TITLE"
                    echo ""
                fi
                
                if [ -n "$CONTENT" ]; then
                    echo "$CONTENT"
                else
                    echo "No content found or content is empty."
                fi
            fi
            """,
            args=[
                Arg(name="page_id", description="ID of the page to retrieve", required=False),
                Arg(name="title", description="Title of the page to retrieve", required=False),
                Arg(name="space_key", description="Space key where the page is located", required=False),
                Arg(name="label", description="Label to filter pages by", required=False),
                Arg(name="limit", description="Maximum number of results to return when filtering by label", required=False)
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
            
            # Basic validation
            validate_confluence_connection
            
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
                # Use v1 API for Atlassian Cloud
                SEARCH_URL="$CONFLUENCE_URL/rest/api/content/search"
                
                # URL encode the query for the CQL query
                ENCODED_QUERY=$(echo "$query" | sed 's/ /%20/g')
                SEARCH_QUERY="text%20~%20%22$ENCODED_QUERY%22"
                
                # Add space key filter if provided
                if [ -n "$space_key" ]; then
                    SEARCH_QUERY="$SEARCH_QUERY%20AND%20space%20=%20$space_key"
                fi
                
                SEARCH_URL="$SEARCH_URL?cql=$SEARCH_QUERY&limit=$LIMIT"
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
                -u "$CONFLUENCE_USERNAME:$CONFLUENCE_API_TOKEN" \
                -H "Accept: application/json")
            
            # Check if we got a valid response
            RESULT_COUNT=$(echo "$SEARCH_RESULT" | jq '.size // 0')
            
            if [ "$RESULT_COUNT" -eq 0 ]; then
                echo "No results found for query: $query"
                exit 0
            fi
            
            echo "Found $RESULT_COUNT results:"
            echo ""
            
            # Display the results
            echo "$SEARCH_RESULT" | jq -r --arg base_url "$CONFLUENCE_URL" '.results[] | "ID: \(.id)\nTitle: \(.title)\nType: \(.type)\nSpace: \(.space.name) (\(.space.key))\nURL: \($base_url)/display/\(.space.key)/\(.id)\n"'
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
            
            # Basic validation
            validate_confluence_connection
            
            # Set limit with default
            LIMIT=${limit:-25}
            
            # Remove trailing slashes from URL
            CONFLUENCE_URL=$(echo "$CONFLUENCE_URL" | sed 's/\/$//')
            
            # For Atlassian Cloud
            if [[ "$CONFLUENCE_URL" == *"atlassian.net"* ]]; then
                # Use v1 API for Atlassian Cloud
                SPACES_URL="$CONFLUENCE_URL/rest/api/space?limit=$LIMIT"
            else
                # For self-hosted Confluence
                SPACES_URL="$CONFLUENCE_URL/rest/api/space?limit=$LIMIT"
            fi
            
            echo "Retrieving list of Confluence spaces..."
            SPACES_RESULT=$(curl -s -X GET "$SPACES_URL" \
                -u "$CONFLUENCE_USERNAME:$CONFLUENCE_API_TOKEN" \
                -H "Accept: application/json")
            
            # Check if we got any results
            RESULT_COUNT=$(echo "$SPACES_RESULT" | jq '.size // 0')
            
            if [ "$RESULT_COUNT" -eq 0 ]; then
                echo "No spaces found or you don't have access to any spaces."
                exit 0
            fi
            
            echo "Found $RESULT_COUNT spaces:"
            echo ""
            
            # Display the results
            echo "$SPACES_RESULT" | jq -r --arg base_url "$CONFLUENCE_URL" '.results[] | "Key: \(.key)\nName: \(.name)\nType: \(.type)\nDescription: \(.description.plain.value // "No description")\nURL: \($base_url)/display/\(.key)\n"'
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
            
            # Basic validation
            validate_confluence_connection
            
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
                # Use v1 API for Atlassian Cloud
                CONTENT_URL="$CONFLUENCE_URL/rest/api/space/$space_key/content?limit=$LIMIT"
            else
                # For self-hosted Confluence
                CONTENT_URL="$CONFLUENCE_URL/rest/api/space/$space_key/content?limit=$LIMIT"
            fi
            
            echo "Retrieving content from space: $space_key"
            CONTENT_RESULT=$(curl -s -X GET "$CONTENT_URL" \
                -u "$CONFLUENCE_USERNAME:$CONFLUENCE_API_TOKEN" \
                -H "Accept: application/json")
            
            # Check if we got a valid response
            if [ "$(echo "$CONTENT_RESULT" | jq -r '.statusCode // ""')" != "" ]; then
                echo "Error: $(echo "$CONTENT_RESULT" | jq -r '.message // "Unknown error"')"
                exit 1
            fi
            
            # Check if we got any results
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
            """,
            args=[
                Arg(name="space_key", description="Space key to get content from", required=True),
                Arg(name="limit", description="Maximum number of results to return", required=False)
            ],
            image="curlimages/curl:8.1.2"
        )

    def get_space_content_analyzer(self) -> ConfluenceTool:
        """Analyze Confluence space content to answer natural language queries."""
        return ConfluenceTool(
            name="confluence_space_content_analyzer",
            description="Analyze content from a Confluence space to answer specific questions using AI. The tool retrieves all content from the specified space, processes it with AI, and provides relevant answers to your query.",
            content="""
            # Install required packages
            pip install -q requests litellm
            
            # Run the analyzer script
            python3 /tmp/space_content_analyzer.py
            """,
            args=[
                Arg(name="space_key", description="Space key to analyze content from", required=True),
                Arg(name="query", description="Natural language query about the content in this space", required=True)
            ],
            env=["LLM_BASE_URL", "KUBIYA_USER_EMAIL"],
            secrets=["LLM_API_KEY"],
            image="python:3.11-slim",
            with_files=[
                FileSpec(
                    destination="/tmp/space_content_analyzer.py",
                    content=inspect.getsource(space_content_analyzer)
                )
            ]
        )

ContentTools() 