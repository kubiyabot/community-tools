"""Python code execution tool."""

from kubiya_sdk.tools import Arg
from .base import PythonExecutorTool

class PythonExecutor(PythonExecutorTool):
    """Python code execution tool."""
    
    def __init__(self):
        super().__init__(
            name="python",
            description="Execute Python code in an isolated environment. Supports dependencies, environment variables, and file creation.",
            content="""
#!/bin/sh
set -e  # Exit on any error

# Enable error handling
error_handler() {
    echo "Error occurred in script at line: ${1}" >&2
    exit 1
}
trap 'error_handler ${LINENO}' ERR

# Function for logging
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# Function to create directories
create_directory() {
    local dir_path="$1"
    log "Creating directory: $dir_path"
    mkdir -p "$dir_path" || { log "ERROR: Failed to create directory: $dir_path"; exit 1; }
}

# Function to create a file with content
create_file() {
    local file_path="$1"
    local content="$2"
    log "Creating file: $file_path"
    mkdir -p "$(dirname "$file_path")" || { log "ERROR: Failed to create parent directory for: $file_path"; exit 1; }
    echo "$content" > "$file_path" || { log "ERROR: Failed to create file: $file_path"; exit 1; }
}

# Validate input
if [ -z "$CODE" ]; then
    log "ERROR: No Python code provided"
    exit 1
fi

# Create temporary directory with error handling
TEMP_DIR=$(mktemp -d) || { log "ERROR: Failed to create temporary directory"; exit 1; }
log "Created temporary directory: $TEMP_DIR"
cd "$TEMP_DIR" || { log "ERROR: Failed to change to temporary directory"; exit 1; }

# Process file structure if provided
if [ ! -z "$FILE_STRUCTURE" ]; then
    # Create directories
    log "Creating directories from file structure..."
    echo "$FILE_STRUCTURE" | jq -r '.directories[]?' | while read -r dir; do
        if [ ! -z "$dir" ]; then
            create_directory "$dir"
        fi
    done

    # Create files
    log "Creating files from file structure..."
    echo "$FILE_STRUCTURE" | jq -r 'try .files | to_entries[] | "\(.key)\n\(.value)"' | while read -r path && read -r content; do
        if [ ! -z "$path" ]; then
            create_file "$path" "$content"
        fi
    done
fi

# Create main Python script with error checking
log "Creating main Python script..."
echo "$CODE" > script.py || { log "ERROR: Failed to create script file"; exit 1; }

# Install requirements if provided
if [ ! -z "$REQUIREMENTS" ]; then
    log "Installing requirements..."
    echo "$REQUIREMENTS" > requirements.txt || { log "ERROR: Failed to create requirements file"; exit 1; }
    pip install -r requirements.txt 2>&1 || { log "ERROR: Failed to install requirements"; exit 1; }
    log "Successfully installed requirements"
fi

# Execute the script with proper error handling
log "Executing Python script..."
if [ ! -z "$ENV_VARS" ]; then
    log "Running with environment variables: $ENV_VARS"
    # shellcheck disable=SC2086
    env $ENV_VARS python -u script.py 2>&1 || { log "ERROR: Script execution failed"; exit 1; }
else
    python -u script.py 2>&1 || { log "ERROR: Script execution failed"; exit 1; }
fi
log "Script execution completed successfully"

# Cleanup
log "Cleaning up..."
cd / || { log "ERROR: Failed to leave temporary directory"; exit 1; }
rm -rf "$TEMP_DIR" || { log "WARNING: Failed to clean up temporary directory: $TEMP_DIR"; }
log "Cleanup completed"
""",
            args=[
                Arg(
                    name="code",
                    type="str",
                    description="Python code to execute",
                    required=True,
                    example='print("Hello World")'
                ),
                Arg(
                    name="requirements",
                    type="str",
                    description="Package requirements (one per line)",
                    required=False,
                    example="requests==2.31.0\npandas==2.1.0"
                ),
                Arg(
                    name="env_vars",
                    type="str",
                    description="Environment variables (space-separated KEY=value pairs)",
                    required=False,
                    example="API_KEY=xyz DEBUG=true"
                ),
                Arg(
                    name="file_structure",
                    type="str",
                    description="JSON defining files and directories to create",
                    required=False,
                    example="""
{
    "files": {
        "script.py": "def main():\\n    print('Hello')",
        "config.yaml": "key: value"
    },
    "directories": ["logs", "data"]
}"""
                )
            ],
            mermaid="""
graph TD
    A[Input] --> B[Setup]
    B --> C[Create Environment]
    C --> D[Process Files]
    D --> E[Install Dependencies]
    E --> F[Execute Code]
    F --> G[Cleanup]

    B --> |Validation| H[Error Handling]
    C --> |Errors| H
    D --> |Errors| H
    E --> |Errors| H
    F --> |Errors| H
    
    subgraph Setup
        B
    end
    
    subgraph Execution
        C
        D
        E
        F
    end
    
    subgraph Error Management
        H --> I[Log Error]
        I --> J[Exit]
    end
"""
        )

# Create singleton instance
python_executor = PythonExecutor()