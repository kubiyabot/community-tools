from kubiya_sdk.tools.models import FileSpec
from pathlib import Path

# Get access handler code
HANDLER_PATH = Path(__file__).parent.parent / 'scripts' / 'access_handler.py'
with open(HANDLER_PATH) as f:
    HANDLER_CODE = f.read()

# Common files needed for AWS access
COMMON_FILES = [
    FileSpec(source="$HOME/.aws/credentials", destination="/root/.aws/credentials"),
    FileSpec(source="$HOME/.aws/config", destination="/root/.aws/config"),
    FileSpec(destination="/opt/scripts/access_handler.py", content=HANDLER_CODE)
]

# Common environment variables
COMMON_ENV = [
    "AWS_PROFILE",
    "KUBIYA_USER_EMAIL",
    "SLACK_API_TOKEN"
] 