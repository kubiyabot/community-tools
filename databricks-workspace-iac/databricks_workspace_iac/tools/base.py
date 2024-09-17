from kubiya_sdk.tools.models import Tool
from ..constants import DATABRICKS_ICON_URL, AWS_FILES

class DatabricksTerraformTool(Tool):
    def __init__(self, name, description, content, args, env, long_running=True, with_files=None):
        super().__init__(
            name=name,
            description=description,
            icon_url=DATABRICKS_ICON_URL,
            type="docker",
            image="hashicorp/terraform:latest",
            content=content,
            args=args,
            env=env,
            long_running=long_running,
            with_files=with_files
        )

class DatabricksAWSTerraformTool(DatabricksTerraformTool):
    def __init__(self, name, description, content, args, env, long_running=True):
        super().__init__(
            name=name,
            description=description,
            content=content,
            args=args,
            env=env,
            long_running=long_running,
            with_files=AWS_FILES
        )