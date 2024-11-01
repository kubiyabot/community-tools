from kubiya_sdk.tools import Tool

DATABRICKS_ICON_URL = "https://www.databricks.com/wp-content/themes/databricks/assets/images/databricks-logo.svg"


class DatabricksApiTool(Tool):
    def __init__(
        self,
        name,
        description,
        content,
        args=[],
        env=[],
        secrets=[],
        long_running=False,
        with_files=None,
        image="alpine:latest",
        mermaid=None,
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
