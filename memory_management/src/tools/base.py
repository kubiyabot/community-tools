from dataclasses import dataclass
from typing import Dict, List, Any, Optional
import json
from kubiya_sdk.tools import Tool, Arg
from kubiya_sdk.tools.registry import tool_registry

MEMORY_ICON_URL = "https://www.onlygfx.com/wp-content/uploads/2022/04/brain-icon-3.png"

@dataclass
class MemorySettings:
    """Memory management configuration settings"""
    backend_type: str = 'hosted'
    neo4j_uri: str = 'bolt://localhost:7687'
    neo4j_username: str = 'neo4j'
    local_path: str = '/data/memory'
    required_packages: List[str] = None
    package_versions: Dict[str, str] = None
    advanced_settings: Dict[str, Any] = None

    def __post_init__(self):
        if self.required_packages is None:
            self.required_packages = [
                'mem0', 'litellm', 'neo4j', 'langchain', 
                'langchain_community', 'langchain_openai',
                'chromadb', 'tiktoken', 'rank_bm25'
            ]
        if self.package_versions is None:
            self.package_versions = {
                'mem0': 'mem0ai==0.1.29'
            }
        if self.advanced_settings is None:
            self.advanced_settings = {
                'use_embeddings': True,
                'chunk_size': 1000,
                'chunk_overlap': 200
            }

class MemoryConfig:
    """Builder for Memory management configuration"""

    DEFAULT_PACKAGE_VERSIONS = {
        'mem0': 'mem0ai==0.1.29',
        'litellm': 'litellm',
        'neo4j': 'neo4j',
        'langchain': 'langchain',
        'langchain_community': 'langchain-community',
        'langchain_openai': 'langchain-openai',
        'chromadb': 'chromadb',
        'tiktoken': 'tiktoken',
        'rank_bm25': 'rank-bm25'
    }

    DEFAULT_ADVANCED_SETTINGS = {
        'use_embeddings': True,
        'chunk_size': 1000,
        'chunk_overlap': 200,
        'similarity_threshold': 0.8,
        'max_tokens': 4000
    }

    @classmethod
    def parse_config(cls, config: Optional[Dict]) -> MemorySettings:
        """Parse and validate configuration"""
        try:
            # If config is a string, try to parse it as JSON
            if isinstance(config, str):
                try:
                    config = json.loads(config)
                except json.JSONDecodeError:
                    print(f"⚠️ Warning: Invalid JSON configuration provided, falling back to hosted mode")
                    return MemorySettings()

            # If no config or empty, return default hosted settings
            if not config:
                print("ℹ️ No configuration provided, using hosted mode")
                return MemorySettings()

            # Parse backend configuration
            backend_type = config.get('backend', 'hosted')
            if backend_type not in ['hosted', 'neo4j', 'local']:
                print(f"⚠️ Warning: Unsupported backend type: {backend_type}, falling back to hosted mode")
                return MemorySettings()

            # Parse package versions
            package_versions = cls.DEFAULT_PACKAGE_VERSIONS.copy()
            if 'package_versions' in config:
                package_versions.update(config['package_versions'])

            # Parse advanced settings
            advanced_settings = cls.DEFAULT_ADVANCED_SETTINGS.copy()
            if 'advanced_settings' in config:
                advanced_settings.update(config['advanced_settings'])

            # Create settings object
            settings = MemorySettings(
                backend_type=backend_type,
                neo4j_uri=config.get('neo4j_uri', 'bolt://localhost:7687'),
                neo4j_username=config.get('neo4j_username', 'neo4j'),
                local_path=config.get('local_path', '/data/memory'),
                package_versions=package_versions,
                advanced_settings=advanced_settings
            )

            return settings

        except Exception as e:
            print(f"⚠️ Warning: Error parsing configuration: {str(e)}, falling back to hosted mode")
            return MemorySettings()

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
        try:
            # Get memory configuration from tool registry
            memory_config = tool_registry.get_tool_config("memory")
            print(f"ℹ️ Using memory configuration: {memory_config}")
        except Exception as e:
            print(f"⚠️ Warning: Could not get memory configuration: {str(e)}, falling back to hosted mode")
            memory_config = None

        # Parse configuration with fallback to hosted mode
        settings = MemoryConfig.parse_config(memory_config)
        print(f"ℹ️ Using backend type: {settings.backend_type}")

        # Add memory arguments
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

        # Build enhanced content with package installation
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
"""

        # Add package installation commands
        for package in settings.required_packages:
            package_version = settings.package_versions.get(package, package)
            enhanced_content += f"""
if ! check_package "{package}"; then
    echo "📦 Installing {package}..."
    su - kubiya -c ". /opt/venv/bin/activate && pip install --quiet {package_version}" > /dev/null 2>&1
fi
"""

        # Add backend-specific configuration
        if settings.backend_type == "neo4j":
            enhanced_content += f"""
# Configure Neo4j
export NEO4J_URI="{settings.neo4j_uri}"
export NEO4J_USER="{settings.neo4j_username}"
export NEO4J_PASSWORD="${{NEO4J_PASSWORD}}"
"""
            secrets = secrets + ["NEO4J_PASSWORD"]
        elif settings.backend_type == "hosted":
            enhanced_content += """
# Configure Mem0 hosted service
export MEM0_API_KEY="${MEM0_API_KEY}"
"""
            secrets = secrets + ["MEM0_API_KEY"]
        else:
            enhanced_content += f"""
# Configure local storage
export MEMORY_BACKEND="local"
export MEMORY_PATH="{settings.local_path}"
"""

        # Add advanced settings
        enhanced_content += """
# Configure advanced settings
"""
        for key, value in settings.advanced_settings.items():
            enhanced_content += f'export MEMORY_{key.upper()}="{value}"\n'

        enhanced_content = enhanced_content + content

        super().__init__(
            name=name,
            description=description,
            icon_url=MEMORY_ICON_URL,
            type="docker",
            image=image,
            content=enhanced_content,
            args=combined_args,
            env=env + ["KUBIYA_USER_EMAIL", "KUBIYA_USER_ORG"],
            secrets=secrets,
            long_running=long_running,
            with_files=with_files,
            mermaid=mermaid,
            with_volumes=with_volumes,
        )
