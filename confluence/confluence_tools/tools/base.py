from typing import List, Optional, Dict, Any
from kubiya_sdk.tools import Tool, Arg, FileSpec

CONFLUENCE_ICON_URL = "https://cdn.worldvectorlogo.com/logos/confluence-1.svg"

DEFAULT_MERMAID = """
```mermaid
classDiagram
    class Tool {
        <<interface>>
        +get_args()
        +get_content()
        +get_image()
    }
    class ConfluenceTool {
        -content: str
        -args: List[Arg]
        -image: str
        +__init__(name, description, content, args, image)
        +get_args()
        +get_content()
        +get_image()
        +get_file_specs()
        +validate_args(args)
        +get_error_message(args)
        +get_environment()
    }
    Tool <|-- ConfluenceTool
```
"""

class ConfluenceTool(Tool):
    """Base class for all Confluence tools."""
    
    name: str
    description: str
    content: str = ""
    args: List[Arg] = []
    image: str = "curlimages/curl:8.1.2"
    icon_url: str = CONFLUENCE_ICON_URL
    type: str = "docker"
    mermaid: str = DEFAULT_MERMAID
    
    def __init__(self, name, description, content, args=None, image="curlimages/curl:8.1.2"):
        # Add helper functions to the content
        helper_functions = """
            # Helper functions for Confluence tools
            validate_confluence_connection() {
                if [ -z "$CONFLUENCE_URL" ]; then
                    echo "Error: CONFLUENCE_URL environment variable is required"
                    exit 1
                fi

                if [ -z "$CONFLUENCE_API_TOKEN" ] || [ -z "$CONFLUENCE_USERNAME" ]; then
                    echo "Error: CONFLUENCE_API_TOKEN and CONFLUENCE_USERNAME environment variables are required"
                    exit 1
                fi
                
                # Create auth header with API token
                AUTH_HEADER="Authorization: Basic $(echo -n "$CONFLUENCE_USERNAME:$CONFLUENCE_API_TOKEN" | base64)"

                # Print connection details for debugging (without exposing the full token)
                echo "Attempting to connect to: $CONFLUENCE_URL"
                echo "Using username: $CONFLUENCE_USERNAME"
                echo "API Token: ${CONFLUENCE_API_TOKEN:0:3}...${CONFLUENCE_API_TOKEN: -3}"
                
                # For Atlassian Cloud, determine the correct API endpoint
                if [[ "$CONFLUENCE_URL" == *"atlassian.net"* ]]; then
                    echo "Detected Atlassian Cloud instance."
                    
                    # Remove trailing slashes
                    CONFLUENCE_URL=$(echo "$CONFLUENCE_URL" | sed 's/\/$//')
                    
                    # Use v2 API for Atlassian Cloud
                    if [[ "$CONFLUENCE_URL" == */wiki ]]; then
                        API_URL="${CONFLUENCE_URL}/api/v2/pages"
                    else
                        API_URL="$CONFLUENCE_URL/wiki/api/v2/pages"
                    fi
                    
                    echo "Using Confluence Cloud v2 API: $API_URL"
                    HTTP_RESPONSE=$(curl -s -w "%{http_code}" -o /dev/null -X GET "$API_URL" \
                        -H "$AUTH_HEADER" \
                        -H "Content-Type: application/json")
                    
                    if [[ "$HTTP_RESPONSE" == "200" ]]; then
                        echo "Successfully connected to Confluence API v2"
                        return 0
                    elif [[ "$HTTP_RESPONSE" == "401" ]]; then
                        echo "Error: Authentication failed. Please check your API token and username."
                        echo "For Atlassian Cloud, create a new API token at: https://id.atlassian.com/manage-profile/security/api-tokens"
                        exit 1
                    else
                        echo "Warning: Received HTTP status $HTTP_RESPONSE from Confluence API"
                        echo "Will continue but operations may fail"
                    fi
                else
                    # For self-hosted Confluence
                    HTTP_RESPONSE=$(curl -s -w "%{http_code}" -o /dev/null -X GET "$CONFLUENCE_URL/rest/api/content" \
                        -H "$AUTH_HEADER" \
                        -H "Content-Type: application/json")
                    
                    if [[ "$HTTP_RESPONSE" == "200" ]]; then
                        echo "Successfully connected to Confluence API"
                        return 0
                    elif [[ "$HTTP_RESPONSE" == "401" ]]; then
                        echo "Error: Authentication failed. Please check your API token and username."
                        exit 1
                    else
                        echo "Warning: Received HTTP status $HTTP_RESPONSE from Confluence API"
                        echo "Will continue but operations may fail"
                    fi
                fi
            }

            get_page_content() {
                local page_id="$1"
                local expand="${2:-body.storage}"
                
                # For Atlassian Cloud, determine the correct API endpoint
                if [[ "$CONFLUENCE_URL" == *"atlassian.net"* ]]; then
                    # Remove trailing slashes
                    CONFLUENCE_URL=$(echo "$CONFLUENCE_URL" | sed 's/\/$//')
                    
                    # Use v2 API for Atlassian Cloud
                    if [[ "$CONFLUENCE_URL" == */wiki ]]; then
                        API_URL="${CONFLUENCE_URL}/api/v2/pages/$page_id?body-format=storage"
                    else
                        API_URL="$CONFLUENCE_URL/wiki/api/v2/pages/$page_id?body-format=storage"
                    fi
                else
                    # For self-hosted Confluence
                    API_URL="$CONFLUENCE_URL/rest/api/content/$page_id?expand=$expand"
                fi
                
                curl -s -X GET "$API_URL" \
                    -H "$AUTH_HEADER" \
                    -H "Content-Type: application/json"
            }

            search_content() {
                local cql="$1"
                local limit="${2:-10}"
                
                # For Atlassian Cloud, determine the correct API endpoint
                if [[ "$CONFLUENCE_URL" == *"atlassian.net"* ]]; then
                    # Remove trailing slashes
                    CONFLUENCE_URL=$(echo "$CONFLUENCE_URL" | sed 's/\/$//')
                    
                    # Use v2 API for Atlassian Cloud
                    if [[ "$CONFLUENCE_URL" == */wiki ]]; then
                        API_URL="${CONFLUENCE_URL}/api/v2/pages?limit=$limit&title=$cql"
                    else
                        API_URL="$CONFLUENCE_URL/wiki/api/v2/pages?limit=$limit&title=$cql"
                    fi
                else
                    # For self-hosted Confluence
                    API_URL="$CONFLUENCE_URL/rest/api/content/search?cql=$cql&limit=$limit"
                fi
                
                curl -s -X GET "$API_URL" \
                    -H "$AUTH_HEADER" \
                    -H "Content-Type: application/json"
            }

            get_space_content() {
                local space_key="$1"
                local limit="${2:-10}"
                
                # For Atlassian Cloud, determine the correct API endpoint
                if [[ "$CONFLUENCE_URL" == *"atlassian.net"* ]]; then
                    # Remove trailing slashes
                    CONFLUENCE_URL=$(echo "$CONFLUENCE_URL" | sed 's/\/$//')
                    
                    # Use v2 API for Atlassian Cloud
                    if [[ "$CONFLUENCE_URL" == */wiki ]]; then
                        API_URL="${CONFLUENCE_URL}/api/v2/spaces/$space_key/pages?limit=$limit"
                    else
                        API_URL="$CONFLUENCE_URL/wiki/api/v2/spaces/$space_key/pages?limit=$limit"
                    fi
                else
                    # For self-hosted Confluence
                    API_URL="$CONFLUENCE_URL/rest/api/space/$space_key/content?limit=$limit"
                fi
                
                curl -s -X GET "$API_URL" \
                    -H "$AUTH_HEADER" \
                    -H "Content-Type: application/json"
            }
        """
        
        content = helper_functions + "\n" + content
        
        super().__init__(
            name=name,
            description=description,
            content=content,
            args=args or [],
            image=image,
            icon_url=CONFLUENCE_ICON_URL,
            type="docker",
            secrets=["CONFLUENCE_API_TOKEN"],
            env=["CONFLUENCE_URL", "CONFLUENCE_USERNAME"]
        )

    def get_args(self) -> List[Arg]:
        """Return the tool's arguments."""
        return self.args

    def get_content(self) -> str:
        """Return the tool's shell script content."""
        return self.content

    def get_image(self) -> str:
        """Return the Docker image to use."""
        return self.image

    def validate_args(self, args: Dict[str, Any]) -> bool:
        """Validate the provided arguments."""
        required_args = [arg.name for arg in self.args if arg.required]
        return all(arg in args and args[arg] for arg in required_args)

    def get_error_message(self, args: Dict[str, Any]) -> Optional[str]:
        """Return error message if arguments are invalid."""
        missing_args = []
        for arg in self.args:
            if arg.required and (arg.name not in args or not args[arg.name]):
                missing_args.append(arg.name)
        
        if missing_args:
            return f"Missing required arguments: {', '.join(missing_args)}"
        return None 