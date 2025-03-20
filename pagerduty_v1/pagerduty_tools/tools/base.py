from typing import List, Optional, Dict, Any
from kubiya_sdk.tools import Tool, Arg, FileSpec
from pydantic import BaseModel

PAGERDUTY_ICON_URL = "https://user-images.githubusercontent.com/113339427/211711571-a01471d5-5405-4876-a129-af0ce48dd2c4.svg"

DEFAULT_MERMAID = """
```mermaid
classDiagram
    class Tool {
        <<interface>>
        +get_args()
        +get_content()
        +get_image()
    }
    class PagerDutyTool {
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
    Tool <|-- PagerDutyTool
```
"""

class PagerDutyTool(Tool):
    """Base class for all PagerDuty tools."""
    
    name: str
    description: str
    content: str = ""
    args: List[Arg] = []
    image: str = "python:3.9-slim"
    icon_url: str = PAGERDUTY_ICON_URL
    type: str = "docker"
    mermaid: str = DEFAULT_MERMAID
    
    def __init__(self, name, description, content, args=None, image="python:3.9-slim"):
        super().__init__(
            name=name,
            description=description,
            content=content,
            args=args or [],
            image=image,
            icon_url=PAGERDUTY_ICON_URL,
            type="docker",
            secrets=["PD_API_KEY"],
            env=["SERVICE_ID", "KUBIYA_USER_EMAIL"]
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