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
            content="""#!/usr/bin/env python3
import os
import sys
import json
import subprocess
import logging
from typing import List, Dict, Any

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def validate_confluence_connection():
    confluence_url = os.environ.get("CONFLUENCE_URL", "")
    username = os.environ.get("CONFLUENCE_USERNAME", "")
    api_token = os.environ.get("CONFLUENCE_API_TOKEN", "")
    
    if not confluence_url or not username or not api_token:
        return False, "Confluence credentials not properly configured"
    
    # Test the connection
    cmd = [
        "curl", "-s",
        "-u", f"{username}:{api_token}",
        "-H", "Accept: application/json",
        f"{confluence_url.rstrip('/')}/rest/api/space?limit=1"
    ]
    
    try:
        process = subprocess.run(cmd, capture_output=True, text=True)
        if process.returncode != 0:
            return False, f"Connection test failed: {process.stderr}"
        
        # Check if the response is valid JSON
        response = json.loads(process.stdout)
        
        # Check for error messages
        if "message" in response:
            return False, f"Confluence API error: {response['message']}"
        
        return True, "Connection successful"
    except Exception as e:
        return False, f"Connection test error: {str(e)}"

# Function to run shell commands
def run_command(cmd):
    try:
        process = subprocess.run(cmd, capture_output=True, text=True)
        if process.returncode != 0:
            logger.error(f"Command error: {process.stderr}")
            return None
        return process.stdout
    except Exception as e:
        logger.error(f"Command execution error: {str(e)}")
        return None

# Get space content
def get_space_content(space_key, limit=None):
    confluence_url = os.environ.get("CONFLUENCE_URL", "").rstrip('/')
    username = os.environ.get("CONFLUENCE_USERNAME", "")
    api_token = os.environ.get("CONFLUENCE_API_TOKEN", "")
    
    # Build the URL
    content_url = f"{confluence_url}/rest/api/space/{space_key}/content"
    if limit:
        content_url += f"?limit={limit}"
    
    # Execute the curl command
    cmd = [
        "curl", "-s",
        "-u", f"{username}:{api_token}",
        "-H", "Accept: application/json",
        content_url
    ]
    
    result = run_command(cmd)
    if not result:
        return None
    
    try:
        return json.loads(result)
    except json.JSONDecodeError:
        logger.error("Error parsing response from Confluence API")
        return None

# Get page content
def get_page_content(page_id):
    confluence_url = os.environ.get("CONFLUENCE_URL", "").rstrip('/')
    username = os.environ.get("CONFLUENCE_USERNAME", "")
    api_token = os.environ.get("CONFLUENCE_API_TOKEN", "")
    
    cmd = [
        "curl", "-s",
        "-u", f"{username}:{api_token}",
        "-H", "Accept: application/json",
        f"{confluence_url}/rest/api/content/{page_id}?expand=body.storage"
    ]
    
    result = run_command(cmd)
    if not result:
        return None
    
    try:
        data = json.loads(result)
        return {
            "id": data.get("id"),
            "title": data.get("title"),
            "content": data.get("body", {}).get("storage", {}).get("value", ""),
            "url": f"{confluence_url}/pages/viewpage.action?pageId={page_id}"
        }
    except json.JSONDecodeError:
        logger.error("Error parsing page content response")
        return None

# Process content with LLM
def process_with_llm(pages, user_query):
    # Install litellm if needed
    try:
        import litellm
    except ImportError:
        logger.info("Installing required packages...")
        subprocess.run(["pip", "install", "-q", "litellm"], check=True)
        import litellm
    
    if not pages:
        return "No content found to process."
    
    # Set up LLM
    litellm.request_timeout = 30
    litellm.num_retries = 3
    
    # Process each page
    all_results = []
    
    for page in pages:
        page_id = page.get("id")
        page_title = page.get("title")
        page_content = page.get("content", "")
        page_url = page.get("url", "")
        
        if not page_content:
            continue
        
        logger.info(f"Processing page: {page_title} (ID: {page_id})")
        
        # Chunk the content if needed
        chunks = chunk_content(page_content)
        page_results = []
        
        for i, chunk in enumerate(chunks):
            # Create prompt for this chunk
            prompt = (
                f"You are analyzing Confluence page content to answer a user query.\n\n"
                f"Page Title: {page_title}\n"
                f"Page URL: {page_url}\n\n"
                f"User Query: {user_query}\n\n"
                f"Content (Chunk {i+1}/{len(chunks)}):\n{chunk}\n\n"
                f"Based on this content, provide a concise answer to the user's query. "
                f"If this chunk doesn't contain relevant information, indicate that briefly."
            )
            
            messages = [
                {"role": "system", "content": "You are a helpful assistant that analyzes Confluence content."},
                {"role": "user", "content": prompt}
            ]
            
            try:
                response = litellm.completion(
                    messages=messages,
                    model="openai/gpt-3.5-turbo",
                    api_key=os.environ.get("LLM_API_KEY", ""),
                    base_url=os.environ.get("LLM_BASE_URL", ""),
                    stream=False,
                    max_tokens=1000,
                    temperature=0.3,
                )
                
                chunk_result = response.choices[0].message.content.strip()
                
                # Only add non-empty and relevant results
                if chunk_result and not chunk_result.lower().startswith("this chunk doesn't contain"):
                    page_results.append({
                        "chunk": i+1,
                        "result": chunk_result
                    })
                
            except Exception as e:
                logger.error(f"Error processing chunk {i+1}: {str(e)}")
                page_results.append({
                    "chunk": i+1,
                    "result": f"Error processing this chunk: {str(e)}"
                })
        
        # Summarize the page results
        if page_results:
            all_results.append({
                "page_title": page_title,
                "page_url": page_url,
                "results": page_results
            })
    
    # If we have results from multiple pages, summarize them
    if len(all_results) > 1:
        # Create a summary of all page results
        summary_prompt = (
            f"You've analyzed multiple Confluence pages to answer this query: '{user_query}'\n\n"
            "Here are the key findings from each page:\n\n"
        )
        
        for page_result in all_results:
            summary_prompt += f"Page: {page_result['page_title']}\n"
            summary_prompt += f"URL: {page_result['page_url']}\n"
            summary_prompt += "Key points:\n"
            
            for chunk_result in page_result['results']:
                summary_prompt += f"- {chunk_result['result']}\n"
            
            summary_prompt += "\n"
        
        summary_prompt += (
            "Based on all this information, provide a comprehensive answer to the user's query. "
            "Include references to specific pages where the information was found."
        )
        
        messages = [
            {"role": "system", "content": "You are a helpful assistant that synthesizes information from multiple sources."},
            {"role": "user", "content": summary_prompt}
        ]
        
        try:
            response = litellm.completion(
                messages=messages,
                model="openai/gpt-3.5-turbo",
                api_key=os.environ.get("LLM_API_KEY", ""),
                base_url=os.environ.get("LLM_BASE_URL", ""),
                stream=False,
                max_tokens=1500,
                temperature=0.3,
            )
            
            final_answer = response.choices[0].message.content.strip()
            return final_answer
            
        except Exception as e:
            logger.error(f"Error creating summary: {str(e)}")
            # Fall back to returning individual page results
            final_answer = f"Error creating summary: {str(e)}\n\nHere are the individual page results:\n\n"
            
            for page_result in all_results:
                final_answer += f"## {page_result['page_title']}\n"
                final_answer += f"URL: {page_result['page_url']}\n\n"
                
                for chunk_result in page_result['results']:
                    final_answer += f"### Chunk {chunk_result['chunk']}:\n{chunk_result['result']}\n\n"
            
            return final_answer
    
    # If we only have one page with results
    elif len(all_results) == 1:
        page_result = all_results[0]
        
        if len(page_result['results']) == 1:
            # If there's only one chunk result, return it directly
            return f"# {page_result['page_title']}\n\n{page_result['results'][0]['result']}\n\nSource: {page_result['page_url']}"
        else:
            # If there are multiple chunks, summarize them
            summary_prompt = (
                f"You've analyzed the Confluence page '{page_result['page_title']}' to answer this query: '{user_query}'\n\n"
                "Here are the key findings from different sections of the page:\n\n"
            )
            
            for chunk_result in page_result['results']:
                summary_prompt += f"Section {chunk_result['chunk']}:\n{chunk_result['result']}\n\n"
            
            summary_prompt += (
                "Based on all this information, provide a comprehensive answer to the user's query."
            )
            
            messages = [
                {"role": "system", "content": "You are a helpful assistant that synthesizes information from multiple sections of a document."},
                {"role": "user", "content": summary_prompt}
            ]
            
            try:
                response = litellm.completion(
                    messages=messages,
                    model="openai/gpt-3.5-turbo",
                    api_key=os.environ.get("LLM_API_KEY", ""),
                    base_url=os.environ.get("LLM_BASE_URL", ""),
                    stream=False,
                    max_tokens=1000,
                    temperature=0.3,
                )
                
                final_answer = response.choices[0].message.content.strip()
                return f"# {page_result['page_title']}\n\n{final_answer}\n\nSource: {page_result['page_url']}"
                
            except Exception as e:
                logger.error(f"Error creating page summary: {str(e)}")
                # Fall back to returning individual chunk results
                final_answer = f"# {page_result['page_title']}\n\nError creating summary: {str(e)}\n\nHere are the individual section results:\n\n"
                
                for chunk_result in page_result['results']:
                    final_answer += f"## Section {chunk_result['chunk']}:\n{chunk_result['result']}\n\n"
                
                final_answer += f"\nSource: {page_result['page_url']}"
                return final_answer
    
    return "No relevant information found in the space content."

# Chunk content into manageable pieces
def chunk_content(content, max_size=8000):
    if len(content) <= max_size:
        return [content]
    
    # Try to split at paragraph boundaries
    paragraphs = content.split('\n\n')
    chunks = []
    current_chunk = ""
    
    for para in paragraphs:
        if len(current_chunk) + len(para) + 2 <= max_size:
            if current_chunk:
                current_chunk += '\n\n'
            current_chunk += para
        else:
            if current_chunk:
                chunks.append(current_chunk)
            
            # If a single paragraph is too large, split it further
            if len(para) > max_size:
                # Split at sentence boundaries
                sentences = para.replace('. ', '.\n').split('\n')
                current_chunk = ""
                
                for sentence in sentences:
                    if len(current_chunk) + len(sentence) + 1 <= max_size:
                        if current_chunk:
                            current_chunk += ' '
                        current_chunk += sentence
                    else:
                        if current_chunk:
                            chunks.append(current_chunk)
                        
                        # If a single sentence is too large, just split it
                        if len(sentence) > max_size:
                            for i in range(0, len(sentence), max_size):
                                chunks.append(sentence[i:i+max_size])
                            current_chunk = ""
                        else:
                            current_chunk = sentence
            else:
                current_chunk = para
    
    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks

def execute_confluence_action(action, **kwargs):
    logger.info(f"Executing Confluence {action} action with params: {kwargs}")
    
    # Validate connection
    valid, message = validate_confluence_connection()
    if not valid:
        return {"success": False, "error": message}
    
    space_key = kwargs.get('space_key')
    limit = kwargs.get('limit')
    query = kwargs.get('query', '')
    
    if not space_key:
        return {"success": False, "error": "Space key is required"}
    
    # Get space content
    logger.info(f"Retrieving content from space: {space_key}")
    content_result = get_space_content(space_key, limit)
    
    if not content_result:
        return {"success": False, "error": f"Failed to retrieve content from space: {space_key}"}
    
    # Check if we got any results
    page_count = content_result.get("page", {}).get("size", 0)
    blog_count = content_result.get("blogpost", {}).get("size", 0)
    
    if page_count == 0 and blog_count == 0:
        return {"success": True, "message": f"No content found in space: {space_key}"}
    
    # If no query, just return the content list
    if not query:
        result = {"success": True, "space_key": space_key}
        
        # Format pages
        if page_count > 0:
            pages = []
            for page in content_result.get("page", {}).get("results", []):
                pages.append({
                    "id": page.get("id"),
                    "title": page.get("title"),
                    "type": page.get("type"),
                    "url": f"{os.environ.get('CONFLUENCE_URL', '').rstrip('/')}/display/{space_key}/{page.get('id')}"
                })
            result["pages"] = pages
            result["page_count"] = page_count
        
        # Format blog posts
        if blog_count > 0:
            blogs = []
            for blog in content_result.get("blogpost", {}).get("results", []):
                blogs.append({
                    "id": blog.get("id"),
                    "title": blog.get("title"),
                    "type": blog.get("type"),
                    "url": f"{os.environ.get('CONFLUENCE_URL', '').rstrip('/')}/display/{space_key}/{blog.get('id')}"
                })
            result["blogs"] = blogs
            result["blog_count"] = blog_count
        
        return result
    else:
        # Process with query
        logger.info(f"Processing query: {query}")
        
        # Get full content of each page
        pages = []
        
        # Extract page IDs and titles
        if "page" in content_result and "results" in content_result["page"]:
            for page in content_result["page"]["results"]:
                page_id = page.get("id")
                if page_id:
                    page_content = get_page_content(page_id)
                    if page_content:
                        pages.append(page_content)
        
        # Process with LLM
        if not pages:
            return {"success": True, "message": "No page content found to process"}
        
        result = process_with_llm(pages, query)
        return {"success": True, "answer": result}

if __name__ == "__main__":
    # Check for required environment variables
    if not os.environ.get("CONFLUENCE_URL") or not os.environ.get("CONFLUENCE_USERNAME") or not os.environ.get("CONFLUENCE_API_TOKEN"):
        logger.error("Confluence credentials not properly configured")
        print(json.dumps({"success": False, "error": "Confluence credentials not properly configured"}))
        sys.exit(1)

    logger.info("Starting Confluence space content execution...")
    
    # Get arguments from environment variables
    args = {}
    for arg in ["space_key", "limit", "query"]:
        if arg in os.environ:
            args[arg] = os.environ[arg]
    
    result = execute_confluence_action("confluence_space_content", **args)
    logger.info("Confluence space content execution completed")
    print(json.dumps(result))
        """,
            args=[
                Arg(name="space_key", description="Space key to analyze content from", required=True),
                Arg(name="query", description="Natural language query about the content in this space", required=True)
            ],
            env=["LLM_BASE_URL", "KUBIYA_USER_EMAIL"],
            secrets=["LLM_API_KEY"],
            image="python:3.11-slim"
        )

ContentTools() 