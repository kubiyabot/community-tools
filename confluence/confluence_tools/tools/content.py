from .base import ConfluenceTool, Arg, ContentAnalyzerTool, ConfluenceToKnowledgeTool
from kubiya_sdk.tools.registry import tool_registry

class ContentTools:
    """Confluence content access and management tools."""

    def __init__(self):
        """Initialize and register all Confluence content tools."""
        tools = [
            self.get_page_content(),
            self.search_content(),
            self.list_spaces(),
            self.get_space_content_analyzer(),
            self.import_space_to_knowledge(),
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

    def get_space_content_analyzer(self) -> ContentAnalyzerTool:
        """Analyze Confluence space content to answer natural language queries."""
        return ContentAnalyzerTool(
            name="confluence_space_content_analyzer",
            description="Analyze content from a Confluence space to answer specific questions using AI. The tool retrieves all content from the specified space, processes it with AI, and provides relevant answers to your query.",
            args=[
                Arg(name="space_key", description="Space key to analyze content from", required=True),
                Arg(name="query", description="Natural language query about the content in this space", required=True)
            ]
        )

    def import_space_to_knowledge(self) -> ConfluenceToKnowledgeTool:
        """Import all content from a Confluence space to Kubiya knowledge."""
        
        # Python script for importing Confluence content to Kubiya knowledge
        python_script = """
import os
import sys
import json
import logging
import requests
import tempfile
import subprocess
from typing import Dict, List, Any, Optional

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def validate_confluence_connection():
    confluence_url = os.environ.get("CONFLUENCE_URL", "")
    username = os.environ.get("CONFLUENCE_USERNAME", "")
    api_token = os.environ.get("CONFLUENCE_API_TOKEN", "")
    
    if not confluence_url or not username or not api_token:
        logger.error("Confluence credentials not properly configured")
        return False
    
    # Test the connection
    try:
        url = f"{confluence_url.rstrip('/')}/rest/api/space?limit=1"
        response = requests.get(
            url,
            auth=(username, api_token),
            headers={"Accept": "application/json"},
            timeout=10
        )
        
        # Check status code
        if response.status_code != 200:
            logger.error(f"Connection test failed: HTTP {response.status_code} - {response.text}")
            return False
        
        # Check if the response is valid JSON
        try:
            data = response.json()
            
            # Check for error messages
            if "message" in data:
                logger.error(f"Confluence API error: {data['message']}")
                return False
            
            logger.info("Confluence connection successful")
            return True
        except ValueError as e:
            logger.error(f"Invalid JSON response from Confluence API: {e}")
            return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Connection test error: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return False

def make_api_request(url, auth_tuple):
    try:
        response = requests.get(
            url,
            auth=auth_tuple,
            headers={"Accept": "application/json"},
            timeout=10
        )
        
        if response.status_code != 200:
            logger.error(f"API request error: HTTP {response.status_code} - {response.text}")
            return None
        
        return response.text
    except Exception as e:
        logger.error(f"API request error: {str(e)}")
        return None

def get_space_content(space_key):
    confluence_url = os.environ.get("CONFLUENCE_URL", "").rstrip('/')
    username = os.environ.get("CONFLUENCE_USERNAME", "")
    api_token = os.environ.get("CONFLUENCE_API_TOKEN", "")
    
    # Build the URL with a higher limit (max is 100 per request)
    content_url = f"{confluence_url}/rest/api/space/{space_key}/content?limit=100"
    
    logger.info(f"Fetching content from space '{space_key}' at URL: {content_url}")
    
    # Make the API request
    result = make_api_request(content_url, (username, api_token))
    if not result:
        return None
    
    try:
        data = json.loads(result)
        
        # Check if we need to paginate for more results
        all_pages = []
        all_blogs = []
        
        # Add initial results
        if "page" in data and "results" in data["page"]:
            all_pages.extend(data["page"]["results"])
            
        if "blogpost" in data and "results" in data["blogpost"]:
            all_blogs.extend(data["blogpost"]["results"])
        
        # Handle pagination for pages if needed
        if "page" in data and "_links" in data["page"] and "next" in data["page"]["_links"]:
            logger.info("More than 100 pages found, retrieving additional pages...")
            next_url = data["page"]["_links"]["next"]
            while next_url:
                full_next_url = f"{confluence_url}{next_url}"
                logger.info(f"Fetching next page batch from: {full_next_url}")
                next_result = make_api_request(full_next_url, (username, api_token))
                if not next_result:
                    break
                    
                try:
                    next_data = json.loads(next_result)
                    if "results" in next_data:
                        all_pages.extend(next_data["results"])
                        
                    # Check if there are more pages
                    if "_links" in next_data and "next" in next_data["_links"]:
                        next_url = next_data["_links"]["next"]
                    else:
                        next_url = None
                except json.JSONDecodeError:
                    logger.error("Error parsing paginated response")
                    next_url = None
        
        # Handle pagination for blogs if needed
        if "blogpost" in data and "_links" in data["blogpost"] and "next" in data["blogpost"]["_links"]:
            logger.info("More than 100 blog posts found, retrieving additional blog posts...")
            next_url = data["blogpost"]["_links"]["next"]
            while next_url:
                full_next_url = f"{confluence_url}{next_url}"
                logger.info(f"Fetching next blog batch from: {full_next_url}")
                next_result = make_api_request(full_next_url, (username, api_token))
                if not next_result:
                    break
                    
                try:
                    next_data = json.loads(next_result)
                    if "results" in next_data:
                        all_blogs.extend(next_data["results"])
                        
                    # Check if there are more blogs
                    if "_links" in next_data and "next" in next_data["_links"]:
                        next_url = next_data["_links"]["next"]
                    else:
                        next_url = None
                except json.JSONDecodeError:
                    logger.error("Error parsing paginated response")
                    next_url = None
        
        # Update the data with all pages and blogs
        if all_pages:
            if "page" not in data:
                data["page"] = {}
            data["page"]["results"] = all_pages
            data["page"]["size"] = len(all_pages)
            
        if all_blogs:
            if "blogpost" not in data:
                data["blogpost"] = {}
            data["blogpost"]["results"] = all_blogs
            data["blogpost"]["size"] = len(all_blogs)
            
        logger.info(f"Total pages retrieved: {len(all_pages)}, Total blogs retrieved: {len(all_blogs)}")
        return data
        
    except json.JSONDecodeError:
        logger.error("Error parsing response from Confluence API")
        return None

def get_page_content(page_id):
    confluence_url = os.environ.get("CONFLUENCE_URL", "").rstrip('/')
    username = os.environ.get("CONFLUENCE_USERNAME", "")
    api_token = os.environ.get("CONFLUENCE_API_TOKEN", "")
    
    url = f"{confluence_url}/rest/api/content/{page_id}?expand=body.storage,metadata.labels"
    
    result = make_api_request(url, (username, api_token))
    if not result:
        return None
    
    try:
        data = json.loads(result)
        
        # Extract labels
        labels = []
        if "metadata" in data and "labels" in data["metadata"] and "results" in data["metadata"]["labels"]:
            for label in data["metadata"]["labels"]["results"]:
                if "name" in label:
                    labels.append(label["name"])
        
        return {
            "id": data.get("id"),
            "title": data.get("title"),
            "content": data.get("body", {}).get("storage", {}).get("value", ""),
            "url": f"{confluence_url}/pages/viewpage.action?pageId={page_id}",
            "labels": ",".join(labels)
        }
    except json.JSONDecodeError:
        logger.error("Error parsing page content response")
        return None

def create_knowledge_item(title, content, labels, space_key):
    try:
        # Create a temporary file for the content
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
            temp_file.write(content)
            content_file_path = temp_file.name
        
        # Prepare labels with confluence space key
        if labels:
            all_labels = f"{labels},confluence,space-{space_key}"
        else:
            all_labels = f"confluence,space-{space_key}"
        
        # Create the knowledge item using Kubiya CLI
        cmd = [
            "/usr/local/bin/kubiya", "knowledge", "create",
            "--name", title,
            "--desc", f"Imported from Confluence space: {space_key}",
            "--labels", all_labels,
            "--content-file", content_file_path,
            "--output", "json"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Clean up the temporary file
        os.unlink(content_file_path)
        
        if result.returncode != 0:
            logger.error(f"Error creating knowledge item: {result.stderr}")
            return None
        
        return result.stdout.strip()
    except Exception as e:
        logger.error(f"Error creating knowledge item: {str(e)}")
        return None

def main():
    # Check for required environment variables
    if not validate_confluence_connection():
        print(json.dumps({"success": False, "error": "Confluence connection failed"}))
        sys.exit(1)
    
    # Get arguments from environment variables
    space_key = os.environ.get("space_key", "")
    include_blogs = os.environ.get("include_blogs", "true").lower() == "true"
    
    if not space_key:
        print(json.dumps({"success": False, "error": "space_key is required"}))
        sys.exit(1)
    
    # Get space content
    content_result = get_space_content(space_key)
    
    if not content_result:
        print(json.dumps({"success": False, "error": f"Failed to retrieve content from space: {space_key}"}))
        sys.exit(1)
    
    # Check if we got any results
    page_count = content_result.get("page", {}).get("size", 0)
    blog_count = content_result.get("blogpost", {}).get("size", 0)
    
    logger.info(f"Found {page_count} pages and {blog_count} blog posts in space '{space_key}'")
    
    if page_count == 0 and blog_count == 0:
        print(json.dumps({"success": True, "message": f"No content found in space: {space_key}"}))
        sys.exit(0)
    
    # Process pages
    imported_count = 0
    failed_count = 0
    
    if page_count > 0:
        logger.info(f"Importing {page_count} pages from space '{space_key}'...")
        
        for idx, page in enumerate(content_result.get("page", {}).get("results", []), 1):
            page_id = page.get("id")
            page_title = page.get("title", "untitled")
            
            if page_id:
                logger.info(f"[{idx}/{page_count}] Processing page: {page_title} (ID: {page_id})")
                page_data = get_page_content(page_id)
                
                if page_data and page_data.get("content"):
                    # Create knowledge item
                    result = create_knowledge_item(
                        page_data["title"],
                        page_data["content"],
                        page_data["labels"],
                        space_key
                    )
                    
                    if result:
                        try:
                            result_json = json.loads(result)
                            if "uuid" in result_json:
                                logger.info(f"✅ Successfully imported page '{page_title}' as knowledge item with UUID: {result_json['uuid']}")
                                imported_count += 1
                            else:
                                logger.error(f"❌ Failed to import page '{page_title}': {result}")
                                failed_count += 1
                        except json.JSONDecodeError:
                            logger.error(f"❌ Failed to import page '{page_title}': Invalid response format")
                            failed_count += 1
                    else:
                        logger.error(f"❌ Failed to import page '{page_title}'")
                        failed_count += 1
                else:
                    logger.error(f"❌ Failed to retrieve content for page '{page_title}'")
                    failed_count += 1
    
    # Process blog posts if requested
    if include_blogs and blog_count > 0:
        logger.info(f"Importing {blog_count} blog posts from space '{space_key}'...")
        
        for idx, blog in enumerate(content_result.get("blogpost", {}).get("results", []), 1):
            blog_id = blog.get("id")
            blog_title = blog.get("title", "untitled")
            
            if blog_id:
                logger.info(f"[{idx}/{blog_count}] Processing blog post: {blog_title} (ID: {blog_id})")
                blog_data = get_page_content(blog_id)
                
                if blog_data and blog_data.get("content"):
                    # Create knowledge item with blog label
                    labels = blog_data["labels"]
                    if labels:
                        labels += ",blog"
                    else:
                        labels = "blog"
                    
                    result = create_knowledge_item(
                        blog_data["title"],
                        blog_data["content"],
                        labels,
                        space_key
                    )
                    
                    if result:
                        try:
                            result_json = json.loads(result)
                            if "uuid" in result_json:
                                logger.info(f"✅ Successfully imported blog post '{blog_title}' as knowledge item with UUID: {result_json['uuid']}")
                                imported_count += 1
                            else:
                                logger.error(f"❌ Failed to import blog post '{blog_title}': {result}")
                                failed_count += 1
                        except json.JSONDecodeError:
                            logger.error(f"❌ Failed to import blog post '{blog_title}': Invalid response format")
                            failed_count += 1
                    else:
                        logger.error(f"❌ Failed to import blog post '{blog_title}'")
                        failed_count += 1
                else:
                    logger.error(f"❌ Failed to retrieve content for blog post '{blog_title}'")
                    failed_count += 1
    
    # Print summary
    summary = {
        "success": True,
        "space_key": space_key,
        "total_content_items": page_count + (blog_count if include_blogs else 0),
        "imported_count": imported_count,
        "failed_count": failed_count
    }
    
    print(json.dumps(summary))

if __name__ == "__main__":
    main()
"""
        
        return ConfluenceToKnowledgeTool(
            name="confluence_import_to_knowledge",
            description="Import all content from a Confluence space into Kubiya knowledge items",
            python_script=python_script,
            args=[
                Arg(name="space_key", description="Key of the Confluence space to import", required=True),
                Arg(name="include_blogs", description="Whether to include blog posts in the import (true/false)", required=False, default="true"),
            ]
        )

ContentTools() 