from kubiya_sdk.tools import Tool, Arg
from kubiya_sdk.tools.models import FileSpec
from typing import List, Dict, Any, Set, ClassVar, Optional, Tuple
import os
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class TerraformerTool(Tool):
    """Base class for reverse Terraform engineering tools."""
    
    SUPPORTED_PROVIDERS: ClassVar[Dict[str, Dict[str, Any]]] = {
        'aws': {
            'env': [
                "AWS_ACCESS_KEY_ID",
                "AWS_SECRET_ACCESS_KEY",
                "AWS_SESSION_TOKEN",
                "AWS_REGION"
            ],
            'files': [
                FileSpec(source="$HOME/.aws/credentials", destination="/root/.aws/credentials"),
                FileSpec(source="$HOME/.aws/config", destination="/root/.aws/config")
            ],
            'secrets': ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"]
        },
        'gcp': {
            'env': ["GOOGLE_CREDENTIALS", "GOOGLE_PROJECT"],
            'files': [
                FileSpec(source="$HOME/.config/gcloud/application_default_credentials.json", 
                        destination="/root/.config/gcloud/application_default_credentials.json")
            ],
            'secrets': ["GOOGLE_CREDENTIALS"]
        },
        'azure': {
            'env': [
                "ARM_CLIENT_ID",
                "ARM_CLIENT_SECRET",
                "ARM_SUBSCRIPTION_ID",
                "ARM_TENANT_ID"
            ],
            'files': [],
            'secrets': [
                "ARM_CLIENT_ID",
                "ARM_CLIENT_SECRET",
                "ARM_SUBSCRIPTION_ID",
                "ARM_TENANT_ID"
            ]
        }
    }
    
    @classmethod
    def is_enabled(cls, config: Dict[str, Any]) -> bool:
        """Check if reverse engineering tools should be enabled based on config."""
        return config.get('enable_reverse_terraform', False)
    
    @classmethod
    def get_enabled_providers(cls, config: Dict[str, Any]) -> Set[str]:
        """Get the list of enabled providers from config."""
        providers = config.get('reverse_terraform_providers', ['aws'])
        if isinstance(providers, str):
            providers = [providers]
        return set(providers) & set(cls.SUPPORTED_PROVIDERS.keys())
    
    def __init__(
        self,
        name: str,
        description: str,
        content: str,
        args: List[Arg],
        provider: str,
        env: List[str] = None,
        files: List[FileSpec] = None,
        secrets: List[str] = None,
        long_running: bool = False
    ):
        # Base Docker image with required tools
        image = "kubiya/terraformer:latest"
        
        # Get provider-specific configurations
        provider_config = self.SUPPORTED_PROVIDERS.get(provider, {})
        
        # Merge provider-specific and custom configurations
        base_env = provider_config.get('env', [])
        if env:
            base_env.extend(env)
            
        base_files = provider_config.get('files', [])
        if files:
            base_files.extend(files)
            
        base_secrets = provider_config.get('secrets', [])
        if secrets:
            base_secrets.extend(secrets)
            
        super().__init__(
            name=name,
            description=description,
            type="docker",
            image=image,
            content=content,
            args=args,
            env=base_env,
            files=base_files,
            secrets=base_secrets,
            long_running=long_running
        )

def _initialize_provider_tools(provider: str, tool_registry) -> Optional[Tuple[Tool, Tool]]:
    """Initialize tools for a specific provider."""
    try:
        # Provider-specific configurations
        PROVIDER_CONFIGS = {
            'aws': {
                'import_cmd': 'terraformer import aws',
                'list_cmd': 'terraformer import aws --list',
                'resource_examples': {
                    'vpc,subnet,ec2': 'networking and compute resources',
                    'rds,elasticache': 'database resources',
                    'iam': 'IAM roles and policies',
                    'lambda,apigateway': 'serverless resources'
                }
            },
            'gcp': {
                'import_cmd': 'terraformer import google',
                'list_cmd': 'terraformer import google --list',
                'resource_examples': {
                    'compute_instances,compute_disks': 'compute resources',
                    'cloudsql,redis': 'database resources',
                    'iam': 'IAM resources',
                    'cloud_functions': 'serverless resources'
                }
            },
            'azure': {
                'import_cmd': 'terraformer import azure',
                'list_cmd': 'terraformer import azure --list',
                'resource_examples': {
                    'virtual_network,subnet': 'networking resources',
                    'virtual_machine': 'compute resources',
                    'mysql,redis': 'database resources',
                    'function_app': 'serverless resources'
                }
            }
        }

        provider_config = PROVIDER_CONFIGS.get(provider)
        if not provider_config:
            raise ValueError(f"Unsupported provider: {provider}")

        # Create import tool
        import_tool = TerraformerTool(
            name=f"reverse_terraform_import_{provider}",
            description=f"""Generate Terraform configurations from existing {provider.upper()} infrastructure.
            
This tool analyzes your existing {provider.upper()} resources and automatically generates Terraform code that matches your current infrastructure. Perfect for:
- Converting existing cloud resources into Infrastructure as Code
- Documenting your current infrastructure setup
- Creating a starting point for infrastructure management
- Migrating manual configurations to Terraform""",
            content=_generate_import_script(provider_config['import_cmd']),
            args=_get_provider_args(provider, provider_config['resource_examples']),
            provider=provider,
            long_running=True
        )

        # Create list tool
        list_tool = TerraformerTool(
            name=f"list_supported_resources_{provider}",
            description=f"""List all {provider.upper()} resource types that can be converted to Terraform code.
            
Shows what types of {provider.upper()} resources can be automatically analyzed and converted into Terraform configurations.""",
            content=f"""
#!/bin/bash
set -e

echo "📋 {provider.upper()} resources that can be converted to Terraform code:"
{provider_config['list_cmd']}
""",
            args=[],
            provider=provider,
            long_running=False
        )

        # Return both tools
        return (import_tool, list_tool)

    except Exception as e:
        logger.error(f"Failed to initialize tools for provider {provider}: {str(e)}")
        return None

def initialize_terraformer_tools(config: Dict[str, Any]) -> List[Tool]:
    """Initialize reverse engineering tools if enabled in config."""
    tools: List[Tool] = []
    
    if not TerraformerTool.is_enabled(config):
        logger.info("Reverse Terraform engineering tools are not enabled in configuration")
        return tools

    enabled_providers = TerraformerTool.get_enabled_providers(config)
    if not enabled_providers:
        logger.info("No providers enabled for reverse Terraform engineering")
        return tools

    logger.info(f"Initializing reverse Terraform engineering tools for providers: {enabled_providers}")
    
    from kubiya_sdk.tools.registry import tool_registry

    for provider in enabled_providers:
        try:
            provider_tools = _initialize_provider_tools(provider, tool_registry)
            if provider_tools:
                tools.extend(provider_tools)
                for tool in provider_tools:
                    tool_registry.register("terraform", tool)
        except Exception as e:
            logger.error(f"Failed to initialize tools for provider {provider}: {str(e)}")
            continue

    logger.info("Successfully initialized reverse Terraform engineering tools")
    return tools

def _generate_import_script(import_cmd: str) -> str:
    """Generate the import script for a provider."""
    return """#!/bin/bash
set -e

# Initialize working directory
WORK_DIR="/terraform"
mkdir -p $WORK_DIR
cd $WORK_DIR

# Prepare resource list
IFS=',' read -ra RESOURCES <<< "$resources"
RESOURCE_FLAGS=""
for resource in "${RESOURCES[@]}"; do
    RESOURCE_FLAGS="$RESOURCE_FLAGS --resources=$resource"
done

# Prepare filter flags
FILTER_FLAGS=""
if [ -n "$filter" ]; then
    IFS=',' read -ra FILTERS <<< "$filter"
    for f in "${FILTERS[@]}"; do
        FILTER_FLAGS="$FILTER_FLAGS --filter=$f"
    done
fi

echo "🔍 Starting infrastructure analysis and Terraform code generation..."
echo "Resources to analyze: $resources"
if [ -n "$filter" ]; then
    echo "Filters: $filter"
fi

# Run import
""" + f"{import_cmd}" + """ $RESOURCE_FLAGS $FILTER_FLAGS \
    --path-pattern "{output}/{provider}_{service}" \
    --compact --verbose

# Check for successful import
if [ $? -eq 0 ]; then
    echo "✅ Successfully generated Terraform configurations"
    
    # List generated files
    echo -e "\n📁 Generated Terraform files:"
    find . -type f -name "*.tf" -o -name "*.tfstate" | while read -r file; do
        echo "  - $file"
        echo -e "\n📄 Contents of $file:"
        cat "$file"
        echo -e "\n---"
    done
else
    echo "❌ Failed to generate Terraform configurations"
    exit 1
fi
"""

def _get_provider_args(provider: str, resource_examples: Dict[str, str]) -> List[Arg]:
    """Get provider-specific arguments."""
    examples = "\n".join([f"- '{k}' for {v}" for k, v in resource_examples.items()])
    
    args = [
        Arg(
            name="resources",
            type="str",
            description=f"""{provider.upper()} resource types to analyze and convert to Terraform code.
Examples:
{examples}""",
            required=True
        ),
        Arg(
            name="filter",
            type="str",
            description="""Optional filters to narrow down which resources to include.
Examples:
- 'Name=production-*' for resources with names starting with 'production-'
- 'Environment=prod' for resources tagged with Environment=prod""",
            required=False
        )
    ]
    
    # Add provider-specific args
    if provider == 'aws':
        args.append(
            Arg(
                name="region",
                type="str",
                description="AWS region where your resources are located (e.g., 'us-west-2', 'eu-central-1')",
                required=False
            )
        )
    elif provider == 'gcp':
        args.append(
            Arg(
                name="project",
                type="str",
                description="GCP project ID where your resources are located",
                required=True
            )
        )
    
    return args

__all__ = ['TerraformerTool', 'initialize_terraformer_tools', '_initialize_provider_tools'] 