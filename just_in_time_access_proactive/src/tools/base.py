from kubiya_sdk.tools import Tool

JIT_ICON_URL = "https://kubiya-public-20221113173935726800000003.s3.us-east-1.amazonaws.com/Knite.png"


class JustInTimeAccessTool(Tool):
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
            icon_url=JIT_ICON_URL,
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
