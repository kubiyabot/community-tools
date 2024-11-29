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
        # Add OpenAI configuration for GPT-4-O
        enhanced_content = """
# Configure OpenAI
export OPENAI_API_KEY=$LLM_API_KEY
export OPENAI_API_BASE=https://llm-proxy.kubiya.ai

# Create and activate virtual environment
python -m venv /opt/venv > /dev/null
. /opt/venv/bin/activate > /dev/null

# Install required packages
pip install --upgrade pip > /dev/null
pip install mem0ai[graph] langchain-community rank_bm25 neo4j openai 2>&1 | grep -v '[notice]' > /dev/null

""" + content

        super().__init__(
            name=name,
            description=description,
            icon_url=MEMORY_ICON_URL,
            type="docker",
            image=image,
            content=enhanced_content,
            args=args,
            env=env + ["OPENAI_API_VERSION"],
            secrets=secrets + ["LLM_API_KEY"],
            long_running=long_running,
            with_files=with_files,
            mermaid=mermaid,
            with_volumes=with_volumes,
        )
