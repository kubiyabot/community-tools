from kubiya_sdk.tools import Tool

MEMORY_ICON_URL = "https://path_to_icon/memory_icon.png"

class MemoryManagementTool(Tool):
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
        image="python:3.11-slim",
        mermaid=None,
        with_volumes=None,
    ):
        super().__init__(
            name=name,
            description=description,
            icon_url=MEMORY_ICON_URL,
            type="docker",
            image=image,
            content=content,
            args=args,
            env=env,
            secrets=secrets,
            long_running=long_running,
            with_files=with_files,
            mermaid=mermaid,
            with_volumes=with_volumes,
        ) 