import logging
from kubiya_sdk.tools.models import Tool, FileSpec
from .common import COMMON_FILES, COMMON_ENV

logger = logging.getLogger(__name__)

AWS_ICON = "https://d2908q01vomqb2.cloudfront.net/22d200f8670dbdb3e253a90eee5098477c95c23d/2018/09/24/aws-icon-service-IAM_PERMISSIONS.png"

class AWSJITTool(Tool):
    """Base class for AWS JIT access tools."""
    def __init__(self, **kwargs):
        # Combine with common files and env
        files = list(COMMON_FILES)
        if kwargs.get('with_files'):
            files.extend(kwargs['with_files'])

        env_vars = list(COMMON_ENV)
        if kwargs.get('env'):
            env_vars.extend(kwargs['env'])

        kwargs['type'] = "docker"
        kwargs['image'] = "amazon/aws-cli:latest"
        kwargs['icon_url'] = AWS_ICON
        kwargs['with_files'] = files
        kwargs['env'] = env_vars

        super().__init__(**kwargs)
