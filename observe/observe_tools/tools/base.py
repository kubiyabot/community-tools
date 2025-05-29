from typing import List, Optional, Dict, Any
from kubiya_sdk.tools import Tool, Arg, FileSpec

OBSERVE_ICON_URL = "https://cdn.worldvectorlogo.com/logos/observe.svg"

DEFAULT_MERMAID = """
```mermaid
classDiagram
    class Tool {
        <<interface>>
        +get_args()
        +get_content()
        +get_image()
    }
    class ObserveTool {
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
    Tool <|-- ObserveTool
```
"""

class ObserveTool(Tool):
    """Base class for all Observe platform tools."""
    
    name: str
    description: str
    content: str = ""
    args: List[Arg] = []
    image: str = "alpine:latest"
    icon_url: str = OBSERVE_ICON_URL
    type: str = "docker"
    mermaid: str = DEFAULT_MERMAID
    
    def __init__(self, name, description, content, args=None, image="alpine:latest"):
        """Initialize the Observe tool with common parameters and helper functions."""
        # Add helper functions to the content
        helper_functions = """
            # Helper functions for Observe platform tools
            validate_observe_auth() {
                if [ -z "$OBSERVE_CUSTOMER_ID" ] || [ -z "$OBSERVE_API_KEY" ]; then
                    echo "Error: OBSERVE_CUSTOMER_ID and OBSERVE_API_KEY environment variables are required"
                    exit 1
                fi
            }

            format_timestamp() {
                local timestamp="$1"
                if [ -z "$timestamp" ]; then
                    date -u '+%Y-%m-%dT%H:%M:%SZ'
                else
                    echo "$timestamp"
                fi
            }

            # Function to query Observe datasets
            query_dataset() {
                local dataset_id="$1"
                local query="$2"
                local start_time="$3"
                local end_time="$4"
                
                if [ -z "$start_time" ]; then
                    start_time=$(date -u -d '1 hour ago' '+%Y-%m-%dT%H:%M:%SZ')
                fi
                
                if [ -z "$end_time" ]; then
                    end_time=$(date -u '+%Y-%m-%dT%H:%M:%SZ')
                fi
                
                curl -s -X POST "https://api.observeinc.com/v1/customers/$OBSERVE_CUSTOMER_ID/datasets/$dataset_id/query" \
                    -H "Authorization: Bearer $OBSERVE_API_KEY" \
                    -H "Content-Type: application/json" \
                    -d "{
                        \"query\": \"$query\",
                        \"start\": \"$start_time\",
                        \"end\": \"$end_time\"
                    }"
            }

            # Function to retrieve events from a dataset
            get_events() {
                local dataset_id="$1"
                local start_time="$2"
                local end_time="$3"
                local filter="$4"
                local limit="$5"
                
                if [ -z "$start_time" ]; then
                    start_time=$(date -u -d '1 hour ago' '+%Y-%m-%dT%H:%M:%SZ')
                fi
                
                if [ -z "$end_time" ]; then
                    end_time=$(date -u '+%Y-%m-%dT%H:%M:%SZ')
                fi
                
                if [ -z "$limit" ]; then
                    limit=100
                fi
                
                local filter_param=""
                if [ -n "$filter" ]; then
                    filter_param=", \"filter\": \"$filter\""
                fi
                
                curl -s -X POST "https://api.observeinc.com/v1/customers/$OBSERVE_CUSTOMER_ID/datasets/$dataset_id/events" \
                    -H "Authorization: Bearer $OBSERVE_API_KEY" \
                    -H "Content-Type: application/json" \
                    -d "{
                        \"start\": \"$start_time\",
                        \"end\": \"$end_time\",
                        \"limit\": $limit$filter_param
                    }"
            }

            # Function to retrieve monitor information
            get_monitor() {
                local monitor_id="$1"
                
                curl -s -X GET "https://api.observeinc.com/v1/customers/$OBSERVE_CUSTOMER_ID/monitors/$monitor_id" \
                    -H "Authorization: Bearer $OBSERVE_API_KEY" \
                    -H "Content-Type: application/json"
            }

            # Function to retrieve alert information
            get_alert() {
                local alert_id="$1"
                
                curl -s -X GET "https://api.observeinc.com/v1/customers/$OBSERVE_CUSTOMER_ID/alerts/$alert_id" \
                    -H "Authorization: Bearer $OBSERVE_API_KEY" \
                    -H "Content-Type: application/json"
            }
            
            # Function to list available datasets
            list_datasets() {
                curl -s -X GET "https://api.observeinc.com/v1/customers/$OBSERVE_CUSTOMER_ID/datasets" \
                    -H "Authorization: Bearer $OBSERVE_API_KEY" \
                    -H "Content-Type: application/json"
            }
        """
        
        content = helper_functions + "\n\n" + content
        
        super().__init__(
            name=name,
            description=description,
            content=content,
            args=args or [],
            image=image,
            icon_url=OBSERVE_ICON_URL,
            type="docker",
            secrets=["OBSERVE_API_KEY", "OBSERVE_CUSTOMER_ID"],
            env=["OBSERVE_DATASET_ID"]
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