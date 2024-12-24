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
    
    # Define supported providers and their configurations
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
            # Store name for use in script generation
            self._tool_name = name
            
            # Ensure env is a list
            env = env or []
            if isinstance(env, str):
                env = [env]
            
            # Get provider from name
            provider = name.split('_')[-1] if '_' in name else None
            
            # Create mermaid diagram string
            if 'import' in name:
                mermaid = """
                    graph TD
                        A[Start] --> B[Validate Provider]
                        B --> C[Check Environment]
                        C --> D[Import Resources]
                        D --> E[Generate Terraform Code]
                        E --> F[Save to Directory]
                        F --> G[End]
                """
            else:  # scan
                mermaid = """
                    graph TD
                        A[Start] --> B[Validate Provider]
                        B --> C[Check Environment]
                        C --> D[Scan Infrastructure]
                        D --> E[Generate Report]
                        E --> F[End]
                """

            # Generate scripts before initialization
            wrapper_script = self._generate_wrapper_script(provider)
            terraformer_script = self._get_script_content('terraformer.sh')
            commands_script = self._get_script_content('terraformer_commands.py')

            # Initialize base tool with proper schema
            super().__init__(
                name=name,
                description=description,
                args=args,
                env=env,
                type="docker",
                image="hashicorp/terraform:latest",
                handler=self.handle_terraform_command,
                with_files={
                    '/usr/local/bin/terraformer.sh': {
                        'content': terraformer_script,
                        'mode': '0755'
                    },
                    '/usr/local/bin/terraformer_commands.py': {
                        'content': commands_script,
                        'mode': '0755'
                    },
                    '/usr/local/bin/wrapper.sh': {
                        'content': wrapper_script,
                        'mode': '0755'
                    }
                },
                mermaid=mermaid
            )

        except Exception as e:
            logger.error(f"Failed to initialize TerraformerTool: {str(e)}")
            raise ValueError(f"Tool initialization failed: {str(e)}")

    def _get_script_content(self, script_name: str) -> str:
        """Get the content of a script file."""
        try:
            script_path = Path(__file__).parent.parent / 'scripts' / script_name
            with open(script_path, 'r') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to read script {script_name}: {str(e)}")
            raise ValueError(f"Failed to read script {script_name}")

    def _generate_wrapper_script(self, provider: str) -> str:
        """Generate the wrapper script content."""
        if not provider or provider not in self.SUPPORTED_PROVIDERS:
            env_exports = ""
        else:
            env_vars = self.SUPPORTED_PROVIDERS[provider]['env_vars']
            env_exports = '\n'.join(f'export {var}="${{{var}}}"' for var in env_vars)

        return f"""#!/bin/bash
set -e

# Export environment variables from args
{env_exports}

# Make scripts executable
chmod +x /usr/local/bin/terraformer.sh
chmod +x /usr/local/bin/terraformer_commands.py

# Execute terraformer script
/usr/local/bin/terraformer.sh "$@"
"""

    @handle_script_error
    async def handle_terraform_command(self, **kwargs) -> Dict[str, Any]:
        """Handle terraform commands by delegating to the shell script."""
        try:
            # Extract command type and provider from tool name
            parts = self._tool_name.split('_')
            command_type = parts[1] if len(parts) > 1 else "scan"
            provider = parts[2] if len(parts) > 2 else "aws"

            # Convert kwargs to environment variables
            env = os.environ.copy()
            for key, value in kwargs.items():
                env[key.upper()] = str(value)

            # Add provider-specific environment variables
            if provider in self.SUPPORTED_PROVIDERS:
                for var in self.SUPPORTED_PROVIDERS[provider]['env_vars']:
                    if var in kwargs:
                        env[var] = str(kwargs[var])

            # Build command arguments
            cmd_args = ['/usr/local/bin/wrapper.sh', command_type, provider]
            
            if command_type == 'import':
                cmd_args.extend([
                    kwargs.get('resource_type', 'vpc'),
                    kwargs.get('resource_id', ''),
                    kwargs.get('output_dir', 'terraform_imported')
                ])
            else:  # scan
                cmd_args.extend([
                    kwargs.get('resource_types', 'all'),
                    kwargs.get('output_format', 'hcl')
                ])

            logger.info(f"Executing command: {' '.join(cmd_args)}")
            logger.debug(f"Environment variables: {env}")

            # Execute the script with environment variables
            result = subprocess.run(
                cmd_args,
                env=env,
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
            logger.error(f"Command failed: {e.stderr}")
            raise ScriptError(f"Command failed: {e.stderr}")
        except Exception as e:
            logger.error(f"Failed to handle terraform command: {str(e)}")
            raise ScriptError(str(e))

    class Config:
        arbitrary_types_allowed = True

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
                        type="str",
                        required=True
                    ),
                    Arg(
                        name="resource_id",
                        description="ID or name of the resource to import",
                        type="str",
                        required=True
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