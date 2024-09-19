from kubiya_sdk.tools.models import Tool
from .constants import DATABRICKS_ICON_URL, AWS_ENV, AZURE_ENV

class DatabricksTerraformTool(Tool):
    def __init__(self, name, description, content, args, env, long_running=True, with_files=None, image="hashicorp/terraform:latest", mermaid=None):
        super().__init__(
            name=name,
            description=description,
            icon_url=DATABRICKS_ICON_URL,
            type="docker",
            image=image,
            content=content,
            args=args,
            env=env,
            long_running=long_running,
            with_files=with_files,
            mermaid=mermaid
        )

class DatabricksAWSTerraformTool(DatabricksTerraformTool):
    def __init__(self, name, description, content, args, long_running=True, mermaid=None):
        super().__init__(
            name=name,
            description=description,
            content=content,
            args=args,
            long_running=long_running,
            env=AWS_ENV,
            mermaid=mermaid,
        )

class DatabricksAzureTerraformTool(DatabricksTerraformTool):
    def __init__(self, name, description, content, args, long_running=True, mermaid=None):
        super().__init__(
            name=name,
            description=description,
            content=content,
            args=args,
            env=AZURE_ENV,
            long_running=long_running,
            mermaid=mermaid,
        )