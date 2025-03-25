from kubiya_sdk.tools.models import Tool
from .common import COMMON_FILES, COMMON_ENV

AWS_ICON_URL = "https://upload.wikimedia.org/wikipedia/commons/thumb/9/93/Amazon_Web_Services_Logo.svg/2560px-Amazon_Web_Services_Logo.svg.png"

class AWSCliTool(Tool):
    def __init__(self, name, description, content, args, long_running=False, mermaid_diagram=None):
        # Add LocalStack endpoint configuration
        localstack_content = """
        # Configure AWS CLI endpoint
        ENDPOINT_ARGS="--endpoint-url $AWS_ENDPOINT_URL"
        
        # Replace aws commands with endpoint configuration
        """ + content.replace("aws ", "aws $ENDPOINT_ARGS ")

        super().__init__(
            name=name,
            description=description,
            icon_url=AWS_ICON_URL,
            type="docker",
            image="amazon/aws-cli:latest",
            content=localstack_content,
            args=args,
            with_files=COMMON_FILES,
            env=["AWS_ENDPOINT_URL", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_DEFAULT_REGION"],
            long_running=long_running,
            mermaid_diagram=mermaid_diagram
        )

class AWSSdkTool(Tool):
    def __init__(self, name, description, content, args, long_running=False, mermaid_diagram=None):
        # Add LocalStack endpoint configuration
        localstack_content = """
import os
import boto3

# Configure boto3 with endpoint URL
def create_client(*args, **kwargs):
    return boto3.client(
        *args,
        **kwargs,
        endpoint_url=os.environ['AWS_ENDPOINT_URL']
    )

def create_resource(*args, **kwargs):
    return boto3.resource(
        *args,
        **kwargs,
        endpoint_url=os.environ['AWS_ENDPOINT_URL']
    )

boto3.client = create_client
boto3.resource = create_resource

""" + content

        super().__init__(
            name=name,
            description=description,
            icon_url=AWS_ICON_URL,
            type="python",
            content=localstack_content,
            args=args,
            requirements=["boto3"],
            with_files=COMMON_FILES,
            env=["AWS_ENDPOINT_URL", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_DEFAULT_REGION"],
            long_running=long_running,
            mermaid=mermaid_diagram
        )
