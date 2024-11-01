from kubiya_sdk.tools import Tool
from typing import Optional, List, Dict, Any

DATABRICKS_ICON_URL = "https://www.databricks.com/wp-content/themes/databricks/assets/images/databricks-logo.svg"


class DatabricksApiTool(Tool):
    def __init__(
        self,
        *,
        name: str,
        description: str,
        content: str,
        args: List[Any],
        env: List[Any],
        secrets: List[Any],
        long_running: bool = False,
        with_files: Optional[Dict[str, Any]] = None,
        image: str = "alpine:latest",
        mermaid: Optional[str] = None,
    ):
        super().__init__(
            name=name,
            description=description,
            icon_url=DATABRICKS_ICON_URL,
            type="docker",
            image=image,
            content=content,
            args=args,
            env=env,
            secrets=secrets,
            long_running=long_running,
            with_files=with_files,
            mermaid=mermaid,
        )
