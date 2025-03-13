from typing import List, Optional, Dict, Any
from kubiya_sdk.tools import Tool, Arg, FileSpec

LAUNCHDARKLY_ICON_URL = "https://launchdarkly.com/favicon.ico"

DEFAULT_MERMAID = """
```mermaid
classDiagram
    class Tool {
        <<interface>>
        +get_args()
        +get_content()
        +get_image()
    }
    class LaunchDarklyTool {
        -content: str
        -args: List[Arg]
        -image: str
        +__init__(name, description, content, args, image)
        +get_args()
        +get_content()
        +get_image()
        +validate_args(args)
        +get_error_message(args)
    }
    Tool <|-- LaunchDarklyTool
```
"""

class LaunchDarklyTool(Tool):
    """Base class for all LaunchDarkly tools."""
    
    name: str
    description: str
    content: str = ""
    args: List[Arg] = []
    image: str = "curlimages/curl:8.1.2"
    icon_url: str = LAUNCHDARKLY_ICON_URL
    type: str = "docker"
    mermaid: str = DEFAULT_MERMAID
    
    def __init__(self, name, description, content, args=None, image="curlimages/curl:8.1.2"):
        # Add helper functions to the content
        helper_functions = """
            # Helper functions for LaunchDarkly tools
            validate_launchdarkly_connection() {
                if [ -z "$LD_API_KEY" ]; then
                    echo "Error: LD_API_KEY environment variable is not set"
                    exit 1
                fi

                if [ -z "$PROJECT_KEY" ]; then
                    echo "Error: PROJECT_KEY environment variable is not set"
                    exit 1
                fi

                # Test connection
                if ! curl -s -f -H "Authorization: $LD_API_KEY" \
                    "https://app.launchdarkly.com/api/v2/projects/$PROJECT_KEY" > /dev/null; then
                    echo "Error: Could not connect to LaunchDarkly API"
                    exit 1
                fi
            }
        """
        
        content = helper_functions + "\n" + content
        
        super().__init__(
            name=name,
            description=description,
            content=content,
            args=args or [],
            image=image,
            icon_url=LAUNCHDARKLY_ICON_URL,
            type="docker",
            secrets=["LD_API_KEY"],
            env=["PROJECT_KEY"]
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