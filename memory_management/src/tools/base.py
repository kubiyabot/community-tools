from kubiya_sdk.tools import Tool, Arg

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
        # Add default memory arguments including required tags
        memory_args = [
            Arg(
                name="memory_content",
                type="str",
                description="The content to store in memory",
                required=True
            ),
            Arg(
                name="tags",
                type="str",
                description="""Tags to categorize the memory. Can be:
                - JSON array: '["tag1", "tag2"]'
                - Comma-separated: "tag1,tag2"
                - Single tag: "tag1" """,
                required=True
            ),
            Arg(
                name="custom_prompt",
                type="str",
                description="Optional custom prompt for entity extraction",
                required=False
            ),
        ]

        # Combine memory args with any additional args
        combined_args = memory_args + args

        # Add both LiteLLM and Mem0 configuration
        enhanced_content = """
# Create virtual environment as non-root user
useradd -m kubiya
chown -R kubiya:kubiya /opt
su - kubiya -c "python -m venv /opt/venv" > /dev/null 2>&1

# Activate virtual environment
. /opt/venv/bin/activate

# Configure LiteLLM
export OPENAI_API_KEY=$LLM_API_KEY
export OPENAI_API_BASE=https://llm-proxy.kubiya.ai

# Function to check if a package is installed
check_package() {
    python -c "import $1" 2>/dev/null
    return $?
}

# First upgrade pip
echo "📦 Upgrading pip..."
su - kubiya -c ". /opt/venv/bin/activate && pip install --quiet --upgrade pip" > /dev/null 2>&1

# Check and install each package
echo "📦 Checking required packages..."

if ! check_package "mem0"; then
    echo "📦 Installing mem0ai..."
    su - kubiya -c ". /opt/venv/bin/activate && pip install --quiet mem0ai==0.1.29" > /dev/null 2>&1
fi

if ! check_package "litellm"; then
    echo "📦 Installing litellm..."
    su - kubiya -c ". /opt/venv/bin/activate && pip install --quiet litellm" > /dev/null 2>&1
fi

if ! check_package "neo4j"; then
    echo "📦 Installing neo4j..."
    su - kubiya -c ". /opt/venv/bin/activate && pip install --quiet neo4j" > /dev/null 2>&1
fi

if ! check_package "langchain"; then
    echo "📦 Installing langchain..."
    su - kubiya -c ". /opt/venv/bin/activate && pip install --quiet langchain" > /dev/null 2>&1
fi

if ! check_package "langchain_community"; then
    echo "📦 Installing langchain-community..."
    su - kubiya -c ". /opt/venv/bin/activate && pip install --quiet langchain-community" > /dev/null 2>&1
fi

if ! check_package "langchain_openai"; then
    echo "📦 Installing langchain-openai..."
    su - kubiya -c ". /opt/venv/bin/activate && pip install --quiet langchain-openai" > /dev/null 2>&1
fi

if ! check_package "chromadb"; then
    echo "📦 Installing chromadb..."
    su - kubiya -c ". /opt/venv/bin/activate && pip install --quiet chromadb" > /dev/null 2>&1
fi

if ! check_package "tiktoken"; then
    echo "📦 Installing tiktoken..."
    su - kubiya -c ". /opt/venv/bin/activate && pip install --quiet tiktoken" > /dev/null 2>&1
fi

# Configure Mem0
export MEM0_API_KEY=$MEM0_API_KEY
export NEO4J_URI=$NEO4J_URI
export NEO4J_USER=$NEO4J_USER
export NEO4J_PASSWORD=$NEO4J_PASSWORD

""" + content

        super().__init__(
            name=name,
            description=description,
            icon_url=MEMORY_ICON_URL,
            type="docker",
            image=image,
            content=enhanced_content,
            args=combined_args,
            env=env + ["KUBIYA_USER_EMAIL", "KUBIYA_USER_ORG", "NEO4J_URI", "NEO4J_USER"],
            secrets=secrets + ["LLM_API_KEY", "MEM0_API_KEY", "NEO4J_PASSWORD"],
            long_running=long_running,
            with_files=with_files,
            mermaid=mermaid,
            with_volumes=with_volumes,
        )
