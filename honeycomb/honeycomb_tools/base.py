from typing import List, Optional, Dict, Any
from kubiya_sdk.tools import Tool, Arg

HONEYCOMB_ICON = "https://www.honeycomb.io/wp-content/themes/honeycomb/assets/images/logo-honeycomb-color.svg"

DEFAULT_MERMAID = """
```mermaid
classDiagram
    class Tool {
        <<interface>>
        +get_args()
        +get_content()
        +get_image()
    }
    class HoneycombTool {
        -content: str
        -args: List[Arg]
        -image: str
        +__init__(name, description, content, args)
        +get_args()
        +get_content()
        +get_image()
    }
    Tool <|-- HoneycombTool
```
"""

class HoneycombTool(Tool):
    """Base class for all Honeycomb tools."""
    
    def __init__(
        self,
        name: str,
        description: str,
        content: str,
        args: List[Arg] = None,
        image: str = "curlimages/curl:8.1.2"
    ):
        # Add helper functions to the content
        helper_functions = """
            # Install required packages
            apk --no-cache add jq python3 py3-pip
            pip3 install requests

            # Helper functions for Honeycomb tools
            validate_honeycomb_connection() {
                if [ -z "$HONEYCOMB_API_KEY" ]; then
                    echo "Error: HONEYCOMB_API_KEY environment variable is not set"
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
            icon_url=HONEYCOMB_ICON,
            type="docker",
            secrets=["HONEYCOMB_API_KEY"],
            mermaid=DEFAULT_MERMAID
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