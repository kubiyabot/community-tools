from dataclasses import dataclass
from typing import Dict, List, Any, Optional
import json
import logging
from kubiya_sdk.tools import Tool, Arg
from kubiya_sdk.tools.registry import tool_registry

logger = logging.getLogger(__name__)

@dataclass
class MemorySettings:
    """Memory management configuration settings"""
    backend_type: str = 'hosted'
    neo4j_uri: str = 'bolt://localhost:7687'
    neo4j_username: str = 'neo4j'
    local_path: str = '/data/memory'

class MemoryConfig:
    """Memory configuration manager"""
    
    @classmethod
    def initialize(cls) -> MemorySettings:
        """Initialize memory configuration from tool registry"""
        try:
            # Get configuration from tool registry
            config = tool_registry.get_tool_config("memory")
            logger.info(f"📝 Received memory configuration: {config}")
            
            if not config:
                logger.warning("⚠️ No configuration provided, using hosted mode")
                return MemorySettings()

            # Parse backend configuration
            backend_type = config.get('backend', 'hosted')
            if backend_type not in ['hosted', 'neo4j', 'local']:
                logger.warning(f"⚠️ Unsupported backend type: {backend_type}, falling back to hosted mode")
                return MemorySettings()

            # Create settings object
            settings = MemorySettings(
                backend_type=backend_type,
                neo4j_uri=config.get('neo4j_uri', 'bolt://localhost:7687'),
                neo4j_username=config.get('neo4j_username', 'neo4j'),
                local_path=config.get('local_path', '/data/memory')
            )

            logger.info(f"✅ Using memory backend: {settings.backend_type}")
            return settings

        except Exception as e:
            logger.error(f"❌ Configuration error: {str(e)}, falling back to hosted mode")
            return MemorySettings()

    @classmethod
    def get_requirements(cls, settings: MemorySettings) -> Dict[str, List[str]]:
        """Get environment and secret requirements based on backend type"""
        env = ["KUBIYA_USER_EMAIL", "KUBIYA_USER_ORG"]
        secrets = []

        if settings.backend_type == 'hosted':
            secrets.append("MEM0_API_KEY")
        elif settings.backend_type == 'neo4j':
            env.extend(["NEO4J_URI", "NEO4J_USER"])
            secrets.append("NEO4J_PASSWORD")

        return {
            "env": env,
            "secrets": secrets
        }

    @classmethod
    def get_packages(cls, settings: MemorySettings) -> List[str]:
        """Get required packages based on backend type"""
        if settings.backend_type == 'hosted':
            return ['mem0ai==0.1.29']
        elif settings.backend_type == 'neo4j':
            return [
                'mem0ai==0.1.29',
                'neo4j',
                'langchain-neo4j'
            ]
        else:  # local
            return [
                'mem0ai==0.1.29',
                'chromadb',
                'tiktoken'
            ]

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
        image="python:3.9-alpine",
        mermaid=None,
        with_volumes=None,
    ):
        # Initialize configuration
        settings = MemoryConfig.initialize()
        
        # Get requirements from base config
        requirements = MemoryConfig.get_requirements(settings)
        env = env + requirements["env"]
        secrets = secrets + requirements["secrets"]

        # Build enhanced content
        enhanced_content = f"""#!/bin/sh
# Install only required system packages
apk add py3-pip --quiet > /dev/null 2>&1

# Configure LiteLLM
export OPENAI_API_KEY=$LLM_API_KEY
export OPENAI_API_BASE=https://llm-proxy.kubiya.ai

# Install required packages
echo "🧠 Connecting to {settings.backend_type} knowledge graph... Let's get those synapses firing! ✨"
"""

        # Add package installation commands
        for package in MemoryConfig.get_packages(settings):
            enhanced_content += f"""
if ! pip show {package} > /dev/null 2>&1; then
    pip install --quiet {package} > /dev/null 2>&1
fi
"""

        # Add backend-specific configuration
        if settings.backend_type == "neo4j":
            enhanced_content += f"""
# Configure Neo4j
export NEO4J_URI="{settings.neo4j_uri}"
export NEO4J_USER="{settings.neo4j_username}"
export NEO4J_PASSWORD="$NEO4J_PASSWORD"
export MEMORY_BACKEND="neo4j"
"""
        elif settings.backend_type == "hosted":
            enhanced_content += """
# Configure Mem0 hosted service
export MEM0_API_KEY="$MEM0_API_KEY"
export MEMORY_BACKEND="hosted"
"""
        else:
            enhanced_content += f"""
# Configure local storage
export MEMORY_BACKEND="local"
export MEMORY_PATH="{settings.local_path}"
"""

        enhanced_content = enhanced_content + content

        super().__init__(
            name=name,
            description=description,
            icon_url="https://www.onlygfx.com/wp-content/uploads/2022/04/brain-icon-3.png",
            type="docker",
            image=image,
            content=enhanced_content,
            args=args,
            env=env,
            secrets=secrets,
            long_running=long_running,
            with_files=with_files,
            mermaid=mermaid,
            with_volumes=with_volumes,
        )
