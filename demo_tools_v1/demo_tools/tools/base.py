from typing import List, Optional, Dict, Any
from kubiya_sdk.tools import Tool, Arg

class DemoTool(Tool):
    """Base class for all demo tools."""
    
    name: str
    description: str
    content: str = ""
    args: List[Arg] = []
    image: str = "curlimages/curl:8.1.2"
    type: str = "docker"
    
    def __init__(self, name, description, content, args=None, image="curlimages/curl:8.1.2"):
        super().__init__(
            name=name,
            description=description,
            content=content,
            args=args or [],
            image=image,
            type="docker",
            secrets=["DD_API_KEY"],
            env=["DD_SITE"]
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