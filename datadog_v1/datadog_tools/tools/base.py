from typing import List, Optional, Dict, Any
from kubiya_sdk.tools import Tool, Arg, FileSpec

DATADOG_ICON_URL = "https://cdn.worldvectorlogo.com/logos/datadog.svg"

DEFAULT_MERMAID = """
```mermaid
classDiagram
    class Tool {
        <<interface>>
        +get_args()
        +get_content()
        +get_image()
    }
    class DatadogTool {
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
    Tool <|-- DatadogTool
```
"""

class DatadogTool(Tool):
    """Base class for all Datadog tools."""
    
    name: str
    description: str
    content: str = ""
    args: List[Arg] = []
    image: str = "datadog/agent:latest"
    icon_url: str = DATADOG_ICON_URL
    type: str = "docker"
    mermaid: str = DEFAULT_MERMAID
    
    def __init__(self, name, description, content, args=None, image="datadog/agent:latest"):
        # Add helper functions to the content
        helper_functions = """
            # Helper functions for Datadog tools
            validate_datadog_connection() {
                if [ -z "$DD_API_KEY" ] || [ -z "$DD_APP_KEY" ]; then
                    echo "Error: DD_API_KEY and DD_APP_KEY environment variables are required"
                    exit 1
                fi

                if [ -z "$DD_SITE" ]; then
                    DD_SITE="datadoghq.com"
                fi

                # Test connection
                if ! curl -X GET "https://api.$DD_SITE/api/v1/validate" \
                    -H "DD-API-KEY: $DD_API_KEY" \
                    -H "DD-APPLICATION-KEY: $DD_APP_KEY"; then
                    echo "Error: Could not connect to Datadog API"
                    exit 1
                fi
            }

            query_metrics() {
                local query="$1"
                local from="$2"
                local to="$3"
                curl -X GET "https://api.$DD_SITE/api/v1/query?query=$query&from=$from&to=$to" \
                    -H "DD-API-KEY: $DD_API_KEY" \
                    -H "DD-APPLICATION-KEY: $DD_APP_KEY"
            }

            get_logs() {
                local query="$1"
                local from="$2"
                local to="$3"
                curl -X POST "https://api.$DD_SITE/api/v2/logs/events/search" \
                    -H "DD-API-KEY: $DD_API_KEY" \
                    -H "DD-APPLICATION-KEY: $DD_APP_KEY" \
                    -H "Content-Type: application/json" \
                    -d "{
                        \"filter\": {
                            \"query\": \"$query\",
                            \"from\": \"$from\",
                            \"to\": \"$to\"
                        }
                    }"
            }
        """
        
        content = helper_functions + "\n" + content
        
        super().__init__(
            name=name,
            description=description,
            content=content,
            args=args or [],
            image=image,
            icon_url=DATADOG_ICON_URL,
            type="docker",
            secrets=["DD_API_KEY", "DD_APP_KEY"],
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