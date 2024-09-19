from kubiya_sdk.tools.models import Tool
from databricks_workspace_iac.tools.constants import DATABRICKS_ICON_URL

class DatabricksTerraformTool(Tool):
    def __init__(self, name, description, content, args, env, long_running=True, with_files=None, image="hashicorp/terraform:latest", mermaid=None, secrets=[]):
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
            mermaid=mermaid,
            secrets=secrets
        )

class DatabricksAWSTerraformTool(DatabricksTerraformTool):
    def __init__(self, name, description, content, args, long_running=True, mermaid=None, env=[], secrets=[]):
        super().__init__(
            name=name,
            description=description,
            content=content,
            args=args,
            long_running=long_running,
            env=env,
            mermaid=mermaid,
            secrets=secrets
        )

class DatabricksAzureTerraformTool(DatabricksTerraformTool):
    def __init__(self, name, description, content, args, long_running=True, mermaid=None, env=[], secrets=[]):
        super().__init__(
            name=name,
            description=description,
            content=content,
            args=args,
            env=env,
            long_running=long_running,
            mermaid=mermaid,
            secrets=secrets
        )