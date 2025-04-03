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
        image: str = "alpine:3.18"
    ):
        # Add helper functions to the content
        helper_functions = """
            # Install minimal required packages
            apk --no-cache add curl jq

            # Helper functions for Honeycomb tools
            validate_honeycomb_connection() {
                if [ -z "$HONEYCOMB_API_KEY" ]; then
                    echo "Error: HONEYCOMB_API_KEY environment variable is not set"
                    exit 1
                fi
            }
            
            # Date calculation using date command
            calculate_time_range() {
                local minutes_ago=$1
                local now=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
                local start_time=$(date -u -d "@$(($(date -u +%s) - minutes_ago * 60))" +"%Y-%m-%dT%H:%M:%SZ")
                echo "$start_time $now"
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