from kubiya_sdk.tools import Tool

MEMORY_ICON_URL = "https://www.onlygfx.com/wp-content/uploads/2022/04/brain-icon-3.png"

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
        # Add Mem0 configuration
        enhanced_content = """
# Install required packages
pip install --upgrade pip > /dev/null
pip install mem0ai==0.1.29 2>&1 | grep -v '[notice]' > /dev/null

# Configure Mem0
export MEM0_API_KEY=$MEM0_API_KEY

""" + content

        super().__init__(
            name=name,
            description=description,
            icon_url=MEMORY_ICON_URL,
            type="docker",
            image=image,
            content=enhanced_content,
            args=args,
            env=env + ["KUBIYA_USER_EMAIL", "KUBIYA_USER_ORG"],
            secrets=secrets + ["MEM0_API_KEY"],
            long_running=long_running,
            with_files=with_files,
            mermaid=mermaid,
            with_volumes=with_volumes,
        )
