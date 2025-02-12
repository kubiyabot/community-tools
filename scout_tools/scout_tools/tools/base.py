from kubiya_sdk.tools import Tool
from kubiya_sdk.tools.models import FileSpec

SCOUT_ICON = "https://raw.githubusercontent.com/nccgroup/ScoutSuite/master/docs/images/scout2_logo.png"

# Common files needed for AWS access
COMMON_FILES = [
    FileSpec(source="$HOME/.aws/credentials", destination="/root/.aws/credentials"),
    FileSpec(source="$HOME/.aws/config", destination="/root/.aws/config"),
]

# Common environment variables
COMMON_ENV = [
    "AWS_PROFILE",
    "AWS_DEFAULT_REGION",
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "AWS_SESSION_TOKEN",
]

class ScoutTool(Tool):
    """Base class for ScoutSuite security assessment tools."""
    def __init__(
        self, 
        name: str, 
        description: str, 
        content: str,
        env: list = None,
        with_files: list = None,
        args: list = None
    ):
        # Setup script to install ScoutSuite and its dependencies
        setup_script = """
# Install system dependencies
apt-get update && \\
    apt-get install -y \\
    python3-pip \\
    python3-venv \\
    python3-dev \\
    build-essential \\
    libssl-dev \\
    libffi-dev \\
    git \\
    jq \\
    curl \\
    unzip

# Install AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" && \\
    unzip awscliv2.zip && \\
    ./aws/install

# Create and activate virtual environment
python3 -m venv /opt/venv
. /opt/venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install \\
    boto3 \\
    botocore \\
    awscli \\
    scoutsuite

# Ensure AWS credentials are properly set up
mkdir -p /root/.aws

# Configure AWS CLI to use the profile
if [ ! -z "$AWS_PROFILE" ]; then
    aws configure set profile.$AWS_PROFILE.region ${AWS_DEFAULT_REGION:-us-east-1}
fi

# Test AWS credentials
echo "Testing AWS credentials..."
aws sts get-caller-identity || {
    echo "❌ Failed to validate AWS credentials"
    exit 1
}
"""

        # Combine setup script with the tool's content
        full_content = setup_script + "\n" + content

        super().__init__(
            name=name,
            description=description,
            icon_url=SCOUT_ICON,
            type="docker",
            image="python:3.12-slim",
            content=full_content,
            env=env or COMMON_ENV,
            with_files=(with_files or []) + COMMON_FILES,
            args=args or []
        )

    def validate_aws_credentials(self):
        """Validate AWS credentials are properly configured."""
        return """
# Validate AWS credentials
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo "❌ Failed to validate AWS credentials"
    exit 1
fi
"""

    def get_aws_profile_config(self):
        """Get AWS profile configuration helper."""
        return """
# Configure AWS profile if specified
if [ ! -z "$AWS_PROFILE" ]; then
    export AWS_SDK_LOAD_CONFIG=1
    if [ ! -z "$AWS_DEFAULT_REGION" ]; then
        aws configure set profile.$AWS_PROFILE.region $AWS_DEFAULT_REGION
    fi
fi
"""

__all__ = ['ScoutTool'] 