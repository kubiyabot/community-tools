from kubiya_sdk.tools import Tool, FileSpec
from pathlib import Path

class AWSJITTool(Tool):
    """Base class for AWS JIT access tools."""
    
    def __init__(self, name: str, description: str, content: str, env: list):
        # Get access handler code
        handler_path = Path(__file__).parent.parent / 'scripts' / 'access_handler.py'
        with open(handler_path) as f:
            handler_code = f.read()
            
        super().__init__(
            name=name,
            description=description,
            type="docker",
            image="amazon/aws-cli:latest",
            content=content,
            env=env,
            with_files=[
                FileSpec(source="$HOME/.aws/credentials", destination="/root/.aws/credentials"),
                FileSpec(source="$HOME/.aws/config", destination="/root/.aws/config"),
                FileSpec(destination="/opt/scripts/access_handler.py", content=handler_code)
            ]
        )