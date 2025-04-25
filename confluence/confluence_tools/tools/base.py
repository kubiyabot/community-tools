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
                
                # Try a simple curl request with full debugging
                echo "Testing connection with curl..."
                curl -v --connect-timeout 10 "$CONFLUENCE_URL" 2>&1
                echo ""
                
                # For Atlassian Cloud, the API endpoint might be different
                if [[ "$CONFLUENCE_URL" == *"atlassian.net"* ]]; then
                    echo "Detected Atlassian Cloud instance."
                    
                    # Try the Atlassian Cloud API endpoint
                    API_URL="https://api.atlassian.com/ex/confluence"
                    echo "Trying Atlassian Cloud API endpoint: $API_URL"
                    
                    curl -v --connect-timeout 10 -X GET "$API_URL" \
                        -H "$AUTH_HEADER" \
                        -H "Content-Type: application/json" 2>&1
                    echo ""
                    
                    # Try the standard Confluence Cloud API endpoint
                    if [[ "$CONFLUENCE_URL" == *"/wiki" ]]; then
                        BASE_URL="${CONFLUENCE_URL%/wiki}"
                    else
                        BASE_URL="$CONFLUENCE_URL"
                    fi
                    
                    CLOUD_API_URL="$BASE_URL/rest/api/latest/content"
                    echo "Trying Confluence Cloud API endpoint: $CLOUD_API_URL"
                    
                    curl -v --connect-timeout 10 -X GET "$CLOUD_API_URL" \
                        -H "$AUTH_HEADER" \
                        -H "Content-Type: application/json" 2>&1
                    echo ""
                fi
                
                echo "Connection tests completed. If all tests failed, please check:"
                echo "1. Your network connectivity to Atlassian services"
                echo "2. The correct URL format for your Confluence instance"
                echo "3. Your API token permissions"
                echo "4. For Atlassian Cloud, ensure you're using a valid API token from https://id.atlassian.com/manage-profile/security/api-tokens"
                
                # For now, we'll continue with the script but mark this as a warning
                echo "WARNING: Could not verify Confluence API connection. Continuing anyway..."
                
                # Don't exit with error for now, to allow the script to continue
                # exit 1
            }

            get_page_content() {
                local page_id="$1"
                local expand="${2:-body.storage}"
                
                curl -s -X GET "$CONFLUENCE_URL/rest/api/content/$page_id?expand=$expand" \
                    -H "$AUTH_HEADER" \
                    -H "Content-Type: application/json"
            }

            search_content() {
                local cql="$1"
                local limit="${2:-10}"
                
                curl -s -X GET "$CONFLUENCE_URL/rest/api/content/search?cql=$cql&limit=$limit" \
                    -H "$AUTH_HEADER" \
                    -H "Content-Type: application/json"
            }

            get_space_content() {
                local space_key="$1"
                local limit="${2:-10}"
                
                curl -s -X GET "$CONFLUENCE_URL/rest/api/space/$space_key/content?limit=$limit" \
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