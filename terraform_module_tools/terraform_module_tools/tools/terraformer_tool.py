from kubiya_sdk.tools import Tool, Arg
from typing import List, Dict, Any, Optional, ClassVar
from typing_extensions import TypedDict
import logging
from pathlib import Path
from ..scripts.error_handler import handle_script_error, ScriptError, logger
import os
import subprocess

logger = logging.getLogger(__name__)

class ProviderConfig(TypedDict):
    name: str
    resources: List[str]
    env_vars: List[str]

class TerraformerTool(Tool):
    """Tool for reverse engineering existing infrastructure into Terraform code."""
    
    # Define supported providers and their configurations using proper type annotation
    SUPPORTED_PROVIDERS: ClassVar[Dict[str, ProviderConfig]] = {
        'aws': {
            'name': 'AWS',
            'resources': ['vpc', 'subnet', 'security-group', 'elb', 'rds', 'iam'],
            'env_vars': ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_REGION']
        },
        'gcp': {
            'name': 'Google Cloud',
            'resources': ['compute', 'storage', 'sql', 'iam'],
            'env_vars': ['GOOGLE_CREDENTIALS', 'GOOGLE_PROJECT']
        },
        'azure': {
            'name': 'Azure',
            'resources': ['compute', 'network', 'storage', 'database'],
            'env_vars': ['AZURE_SUBSCRIPTION_ID', 'AZURE_CLIENT_ID', 'AZURE_CLIENT_SECRET', 'AZURE_TENANT_ID']
        }
    }

    def __init__(self, name: str, description: str, args: List[Arg], env: List[str] = None):
        """Initialize the tool with proper base class initialization."""
        try:
            # Ensure env is a list
            env = env or []
            if isinstance(env, str):
                env = [env]
            
            # Get provider from name
            provider = name.split('_')[-1] if '_' in name else None
            if provider and provider in self.SUPPORTED_PROVIDERS:
                # Add provider's required env vars to the list
                env.extend(self.SUPPORTED_PROVIDERS[provider]['env_vars'])
            
            # Create mermaid diagram based on tool type
            if 'import' in name:
                mermaid = {
                    'graph': """
                        graph TD
                            A[Start] --> B[Validate Provider]
                            B --> C[Check Environment]
                            C --> D[Import Resources]
                            D --> E[Generate Terraform Code]
                            E --> F[Save to Directory]
                            F --> G[End]
                    """
                }
            else:  # scan
                mermaid = {
                    'graph': """
                        graph TD
                            A[Start] --> B[Validate Provider]
                            B --> C[Check Environment]
                            C --> D[Scan Infrastructure]
                            D --> E[Generate Report]
                            E --> F[End]
                    """
                }
            
            super().__init__(
                name=name or "terraform_tool",
                description=description or "Terraform infrastructure tool",
                args=args or [],
                env=list(set(env)),  # Remove duplicates
                type="docker",
                image="hashicorp/terraform:latest",
                handler=self.handle_terraform_command,
                with_files={
                    '/usr/local/bin/terraformer.sh': {
                        'source': 'scripts/terraformer.sh',
                        'mode': '0755'
                    }
                },
                mermaid=mermaid
            )
        except Exception as e:
            logger.error(f"Failed to initialize TerraformerTool: {str(e)}")
            # Provide fallback initialization
            super().__init__(
                name=name or "terraform_tool",
                description="Terraform infrastructure tool (fallback)",
                args=[],
                env=[],
                type="docker",
                image="hashicorp/terraform:latest",
                handler=self.handle_terraform_command
            )

    class Config:
        arbitrary_types_allowed = True

    @handle_script_error
    async def handle_terraform_command(self, **kwargs) -> Dict[str, Any]:
        """Handle terraform commands by delegating to the shell script."""
        try:
            # Extract command type and provider from tool name with fallbacks
            parts = self.name.split('_')
            command_type = parts[1] if len(parts) > 1 else "scan"
            provider = parts[2] if len(parts) > 2 else "aws"  # Default to AWS if not specified

            # Build command arguments
            cmd_args = ['/usr/local/bin/terraformer.sh', command_type, provider]
            
            if command_type == 'import':
                cmd_args.extend([
                    kwargs.get('resource_type', 'vpc'),  # Default to VPC if not specified
                    kwargs.get('resource_id', ''),
                    kwargs.get('output_dir', 'terraform_imported')
                ])
            else:  # scan
                cmd_args.extend([
                    kwargs.get('resource_types', 'all'),
                    kwargs.get('output_format', 'hcl')
                ])

            # Execute the script
            try:
                result = subprocess.run(
                    cmd_args,
                    capture_output=True,
                    text=True,
                    check=True
                )
                return {
                    'success': True,
                    'output': result.stdout,
                    'command': ' '.join(cmd_args),
                    'output_dir': kwargs.get('output_dir') if command_type == 'import' else None
                }
            except subprocess.CalledProcessError as e:
                return {
                    'success': False,
                    'error': e.stderr,
                    'command': ' '.join(cmd_args)
                }
            
        except Exception as e:
            logger.error(f"Failed to handle terraform command: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @classmethod
    def get_enabled_providers(cls, config: Dict[str, Any]) -> List[str]:
        """Get list of enabled providers from configuration."""
        try:
            if not config:
                logger.warning("No configuration provided")
                return []

            # Handle config wrapper
            if 'terraform' not in config and any(
                key in config for key in ['enable_reverse_terraform', 'reverse_terraform_providers']
            ):
                config = {'terraform': config}
            
            terraform_config = config.get('terraform', {})
            if not terraform_config:
                logger.warning("No terraform configuration found")
                return []

            if not terraform_config.get('enable_reverse_terraform'):
                logger.info("Reverse terraform engineering is not enabled")
                return []
            
            providers = terraform_config.get('reverse_terraform_providers', [])
            if isinstance(providers, str):
                providers = [providers]
            
            if not providers:
                logger.warning("No providers specified")
                return []
            
            # Validate providers
            valid_providers = []
            for provider in providers:
                if provider in cls.SUPPORTED_PROVIDERS:
                    valid_providers.append(provider)
                    logger.info(f"✅ Validated provider: {provider}")
                else:
                    logger.warning(f"⚠️ Unsupported provider: {provider}. Supported providers: {list(cls.SUPPORTED_PROVIDERS.keys())}")
            
            return valid_providers
            
        except Exception as e:
            logger.error(f"Error getting enabled providers: {str(e)}")
            return []

def _initialize_provider_tools(provider: str) -> List[Tool]:
    """Initialize tools for a specific provider."""
    tools = []
    try:
        if not provider:
            logger.warning("No provider specified")
            return tools

        if provider not in TerraformerTool.SUPPORTED_PROVIDERS:
            logger.warning(f"Unsupported provider: {provider}")
            return tools

        provider_config = TerraformerTool.SUPPORTED_PROVIDERS[provider]
        logger.info(f"Initializing tools for provider: {provider}")
        
        try:
            # Create import tool
            import_tool = TerraformerTool(
                name=f"terraform_import_{provider}",
                description=f"Import existing {provider_config['name']} infrastructure into Terraform",
                args=[
                    Arg(
                        name="resource_type",
                        description=f"Type of resource to import. Available: {', '.join(provider_config['resources'])}",
                        type="str"
                    ),
                    Arg(
                        name="resource_id",
                        description="ID or name of the resource to import",
                        type="str"
                    ),
                    Arg(
                        name="output_dir",
                        description="Directory to save the generated Terraform code",
                        type="str",
                        required=False,
                        default="terraform_imported"
                    )
                ],
                env=provider_config.get('env_vars', [])
            )
            tools.append(import_tool)
            logger.info(f"✅ Created import tool for {provider}")
            
            # Create scan tool
            scan_tool = TerraformerTool(
                name=f"terraform_scan_{provider}",
                description=f"Scan and discover {provider_config['name']} infrastructure for Terraform import",
                args=[
                    Arg(
                        name="resource_types",
                        description=f"Types of resources to scan. Available: {', '.join(provider_config['resources'])}",
                        type="str",
                        required=False,
                        default="all"
                    ),
                    Arg(
                        name="output_format",
                        description="Output format (json, yaml, or hcl)",
                        type="str",
                        required=False,
                        default="hcl"
                    )
                ],
                env=provider_config.get('env_vars', [])
            )
            tools.append(scan_tool)
            logger.info(f"✅ Created scan tool for {provider}")
            
        except Exception as e:
            logger.error(f"Failed to create tools for provider {provider}: {str(e)}")
            
        return tools
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize tools for provider {provider}: {str(e)}")
        return []

__all__ = ['TerraformerTool', '_initialize_provider_tools'] 