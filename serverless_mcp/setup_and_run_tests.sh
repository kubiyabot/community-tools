#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Setting up environment for serverless_mcp tests...${NC}"

# Define environment variables
VENV_DIR="venv"
CURRENT_DIR=$(pwd)

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 is not installed. Please install Python 3 and try again.${NC}"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv $VENV_DIR
else
    echo -e "${YELLOW}Using existing virtual environment...${NC}"
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source $VENV_DIR/bin/activate

# Install dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
pip install --upgrade pip
pip install -e .  # Install the package in editable/development mode

# Create a mock kubiya_sdk package if needed
if ! pip show kubiya-sdk &> /dev/null; then
    echo -e "${YELLOW}Creating mock kubiya_sdk package for testing...${NC}"
    
    # Create a temporary directory for the mock package
    TEMP_DIR=$(mktemp -d)
    mkdir -p $TEMP_DIR/kubiya_sdk/tools
    
    # Create __init__.py
    cat > $TEMP_DIR/kubiya_sdk/__init__.py << EOL
# Mock Kubiya SDK for testing
EOL

    # Create tools.py with mock classes
    cat > $TEMP_DIR/kubiya_sdk/tools/__init__.py << EOL
# Mock Kubiya SDK tools module
from enum import Enum

class ToolType(Enum):
    PYTHON = "python"
    DOCKER = "docker"
    EXECUTOR = "executor"

class KubiyaArgType(Enum):
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    LIST = "list"
    JSON_OBJECT = "json_object"
    
class Arg:
    def __init__(self, name, description="", type=KubiyaArgType.STRING, required=False, default_value=None):
        self.name = name
        self.description = description
        self.type = type
        self.required = required
        self.default_value = default_value
        
    def dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "type": self.type.name,
            "required": self.required,
            "default_value": self.default_value
        }

class Secret:
    def __init__(self, name, mount_path=None):
        self.name = name
        self.mount_path = mount_path

class ServiceSpec:
    def __init__(self, name, image, exposed_ports=None, env=None, secrets=None, volumes=None):
        self.name = name
        self.image = image
        self.exposed_ports = exposed_ports or []
        self.env = env or {}
        self.secrets = secrets or []
        self.volumes = volumes or []
        
    def dict(self):
        return {
            "name": self.name,
            "image": self.image,
            "exposed_ports": self.exposed_ports,
            "env": self.env,
            "secrets": [s.name for s in self.secrets],
            "volumes": self.volumes
        }

class FileSpec:
    def __init__(self, source, destination):
        self.source = source
        self.destination = destination

class Tool:
    def __init__(self, name, description="", type=ToolType.PYTHON, image="", content="", 
                 args=None, icon_url="", with_services=None, secrets=None, env=None):
        self.name = name
        self.description = description
        self.type = type
        self.image = image
        self.content = content
        self.args = args or []
        self.icon_url = icon_url
        self.with_services = with_services or []
        self.secrets = secrets or []
        self.env = env or {}
EOL

    # Create setup.py for the mock package
    cat > $TEMP_DIR/setup.py << EOL
from setuptools import setup, find_packages

setup(
    name="kubiya-sdk",
    version="0.1.0",
    packages=find_packages(),
    description="Mock Kubiya SDK for testing",
)
EOL

    # Install the mock package
    pip install -e $TEMP_DIR
    
    echo -e "${GREEN}Installed mock kubiya_sdk package${NC}"
fi

# Set PYTHONPATH to include the parent directory
export PYTHONPATH=$CURRENT_DIR:$PYTHONPATH

# Run tests with proper path setup
echo -e "${GREEN}Running tests...${NC}"
python -m unittest discover -s tests

# Deactivate virtual environment
deactivate

echo -e "${GREEN}Tests completed.${NC}" 