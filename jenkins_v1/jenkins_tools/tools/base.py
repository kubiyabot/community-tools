from typing import List, Optional, Dict, Any
from kubiya_sdk.tools import Tool, Arg, FileSpec
from pydantic import BaseModel

JENKINS_ICON_URL = "https://www.jenkins.io/images/logos/jenkins/jenkins.png"

DEFAULT_MERMAID = """
```mermaid
classDiagram
    class Tool {
        <<interface>>
        +get_args()
        +get_content()
        +get_image()
    }
    class JenkinsTool {
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
    Tool <|-- JenkinsTool
```
"""

class JenkinsTool(Tool):
    """Base class for all Jenkins tools."""
    
    name: str
    description: str
    content: str = ""
    args: List[Arg] = []
    image: str = "jenkins/jenkins:lts-jdk11"
    icon_url: str = JENKINS_ICON_URL
    type: str = "docker"
    mermaid: str = DEFAULT_MERMAID
    
    def __init__(self, name, description, content, args=None, image="jenkins/jenkins:lts-jdk11"):
        # Add helper functions for Jenkins operations
        setup_content = """
# Begin helper functions
{
    # Function to validate Jenkins connection
    validate_jenkins_connection() {
        if ! curl -sSf -u "$JENKINS_USER:$JENKINS_TOKEN" "$JENKINS_URL/api/json" > /dev/null; then
            echo "Error: Unable to connect to Jenkins server"
            exit 1
        fi
    }

    # Function to handle errors
    handle_error() {
        local exit_code=$?
        local command=$BASH_COMMAND
        echo "Error: Command '$command' failed with exit code $exit_code"
        exit $exit_code
    }

    # Set error handling
    set -e
    trap 'handle_error' ERR

    # Common utility functions
    get_build_url() {
        local job_name="$1"
        local build_number="$2"
        echo "$JENKINS_URL/job/$job_name/$build_number"
    }

    get_build_status() {
        local job_name="$1"
        local build_number="$2"
        curl -sSf -u "$JENKINS_USER:$JENKINS_TOKEN" "$(get_build_url "$job_name" "$build_number")/api/json" | jq -r '.result'
    }

    get_build_timestamp() {
        local job_name="$1"
        local build_number="$2"
        curl -sSf -u "$JENKINS_USER:$JENKINS_TOKEN" "$(get_build_url "$job_name" "$build_number")/api/json" | jq -r '.timestamp'
    }

    get_build_duration() {
        local job_name="$1"
        local build_number="$2"
        curl -sSf -u "$JENKINS_USER:$JENKINS_TOKEN" "$(get_build_url "$job_name" "$build_number")/api/json" | jq -r '.duration'
    }

    wait_for_build() {
        local job_name="$1"
        local build_number="$2"
        local timeout="${3:-300}"
        
        echo "Waiting for build #$build_number of $job_name to complete..."
        local start_time=$(date +%s)
        while true; do
            local status=$(get_build_status "$job_name" "$build_number")
            if [[ "$status" != "null" && "$status" != "INPROGRESS" ]]; then
                echo "Build completed with status: $status"
                break
            fi
            
            local current_time=$(date +%s)
            if (( current_time - start_time > timeout )); then
                echo "Timeout waiting for build to complete"
                exit 1
            fi
            
            sleep 10
        done
    }
}
"""
        super().__init__(
            name=name,
            description=description,
            content=setup_content + "\n" + content,
            args=args or [],
            image=image,
            icon_url=JENKINS_ICON_URL,
            type="docker",
            secrets=["JENKINS_TOKEN"],
            env=["JENKINS_URL", "JENKINS_USER"]
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

    def get_environment(self) -> Dict[str, str]:
        """Return required environment variables."""
        return {
            "JENKINS_URL": "",
            "JENKINS_USER": "",
            "JENKINS_TOKEN": ""
        } 