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
        image: str = "python:3.9-slim"
    ):
        super().__init__(
            name=name,
            description=description,
            content=content,
            args=args or [],
            image=image,
            icon_url=HONEYCOMB_ICON,
            type="python",
            secrets=["HONEYCOMB_API_KEY"],
            mermaid=DEFAULT_MERMAID
        )

    def get_args(self) -> List[Arg]:
        """Return the tool's arguments."""
        return self.args

    def get_content(self) -> str:
        """Return the tool's Python script content."""
        return self.content

    def get_image(self) -> str:
        """Return the Docker image to use."""
        return self.image 