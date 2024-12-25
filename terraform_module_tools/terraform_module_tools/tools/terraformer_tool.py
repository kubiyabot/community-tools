from kubiya_sdk.tools import Tool, Arg, Volume
from typing import List, Dict, Any, Optional, ClassVar
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
import logging
from pathlib import Path
from ..scripts.error_handler import handle_script_error, ScriptError, logger
import os
import subprocess
import uuid
import re

# Common AWS configuration
AWS_COMMON_FILES = [
    {
        'destination': '/root/.aws/credentials',
        'source': '$HOME/.aws/credentials'
    },
    {
        'destination': '/root/.aws/config',
        'source': '$HOME/.aws/config'
    }
]

# Define AWS_PROFILE once
AWS_COMMON_ENV = ["AWS_PROFILE"]

logger = logging.getLogger(__name__)

class ProviderConfig(TypedDict):
    name: str
    resources: List[str]
    env_vars: List[str]

class TerraformerToolConfig(BaseModel):
    name: str
    description: str
    args: List[Arg]
    env: Optional[List[str]] = Field(default_factory=list)
    provider: Optional[str] = None

def sanitize_email(email: str) -> str:
    """Convert email to a filesystem-safe directory name."""
    if not email:
        return "anonymous"
    # Replace @ and dots with underscores, remove any other special characters
    return re.sub(r'[^a-zA-Z0-9_-]', '_', email.replace('@', '_').replace('.', '_'))

class TerraformerTool(Tool):
    """Tool for reverse engineering existing infrastructure into Terraform code."""
    
    # Remove AWS_PROFILE from provider config since it's in AWS_COMMON_ENV
    SUPPORTED_PROVIDERS: ClassVar[Dict[str, ProviderConfig]] = {
        'aws': {
            'name': 'AWS',
            'resources': ['vpc', 'subnet', 'security-group', 'elb', 'rds', 'iam'],
            'env_vars': []  # Remove AWS_PROFILE from here
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
            # Add print_output to base args with string default
            base_args = [
                Arg(
                    name="print_output",
                    description="Whether to print the generated Terraform code to stdout (true/false)",
                    type="str",
                    required=False,
                    default="true"
                )
            ]
            args = args + base_args

            # Add required environment variables
            required_env = ["KUBIYA_USER_EMAIL"]
            if env:
                env.extend(required_env)
            else:
                env = required_env

            # Validate inputs using Pydantic model
            config = TerraformerToolConfig(
                name=name,
                description=description,
                args=args,
                env=env or [],
                provider=name.split('_')[-1] if '_' in name else None
            )
            
            # Add provider-specific environment variables
            if config.provider in self.SUPPORTED_PROVIDERS:
                config.env.extend(self.SUPPORTED_PROVIDERS[config.provider]['env_vars'])
            
            # Add AWS_PROFILE only once
            if config.provider == 'aws':
                config.env.extend(AWS_COMMON_ENV)

            # Create mermaid diagram string
            if 'import' in config.name:
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
            wrapper_script = self._generate_wrapper_script(config.provider)
            terraformer_script = self._get_script_content('terraformer.sh')
            commands_script = self._get_script_content('terraformer_commands.py')

            # Initialize base tool with proper schema
            super().__init__(
                name=config.name,
                description=config.description,
                args=config.args,
                env=config.env,
                type="docker",
                image="python:3.12-alpine",
                handler=self.handle_terraform_command,
                with_files=[
                    {
                        'destination': '/usr/local/bin/terraformer.sh',
                        'content': terraformer_script,
                    },
                    {
                        'destination': '/usr/local/bin/terraformer_commands.py',
                        'content': commands_script,
                    },
                    {
                        'destination': '/usr/local/bin/wrapper.sh',
                        'content': wrapper_script,
                    },
                    # Add AWS configuration files
                    *AWS_COMMON_FILES
                ],
                with_volumes=[
                    Volume(
                        name="terraform_code",
                        path="/var/lib/terraform"
                    )
                ],
                content=f"""#!/bin/bash
set -e

# Export tool name for command detection
export TOOL_NAME="{config.name}"

# Generate unique workspace directory based on user email and UUID
WORKSPACE_ID="$(python3 -c 'import uuid; print(str(uuid.uuid4()))')"
USER_EMAIL="$(echo "$KUBIYA_USER_EMAIL" | tr '@.' '_')"
USER_DIR="/var/lib/terraform/${USER_EMAIL}_${WORKSPACE_ID}"
mkdir -p "$USER_DIR"

# Determine command type and provider from tool name if not set
if [[ -z "$COMMAND_TYPE" ]]; then
    if [[ "$TOOL_NAME" == *"_import_"* ]]; then
        export COMMAND_TYPE="import"
    else
        export COMMAND_TYPE="scan"
    fi
fi

if [[ -z "$PROVIDER" ]]; then
    for p in aws gcp azure; do
        if [[ "$TOOL_NAME" == *"_$p" ]]; then
            export PROVIDER="$p"
            break
        fi
    done
fi

# Set default values for optional arguments if not set
: "${{RESOURCE_TYPES:=all}}"
: "${{OUTPUT_FORMAT:=hcl}}"
: "${{OUTPUT_DIR:=terraform_imported}}"

# Validate required arguments based on command type
if [[ "$COMMAND_TYPE" == "import" ]]; then
    [[ -z "$RESOURCE_TYPE" ]] && echo "RESOURCE_TYPE is required for import" && exit 1
    [[ -z "$RESOURCE_ID" ]] && echo "RESOURCE_ID is required for import" && exit 1
fi

# Validate provider-specific requirements
case "$PROVIDER" in
    aws)
        [[ -z "$AWS_PROFILE" ]] && echo "AWS_PROFILE is required" && exit 1
        ;;
    gcp)
        [[ -z "$GOOGLE_CREDENTIALS" ]] && echo "GOOGLE_CREDENTIALS is required" && exit 1
        [[ -z "$GOOGLE_PROJECT" ]] && echo "GOOGLE_PROJECT is required" && exit 1
        ;;
    azure)
        [[ -z "$AZURE_SUBSCRIPTION_ID" ]] && echo "AZURE_SUBSCRIPTION_ID is required" && exit 1
        [[ -z "$AZURE_CLIENT_ID" ]] && echo "AZURE_CLIENT_ID is required" && exit 1
        [[ -z "$AZURE_CLIENT_SECRET" ]] && echo "AZURE_CLIENT_SECRET is required" && exit 1
        [[ -z "$AZURE_TENANT_ID" ]] && echo "AZURE_TENANT_ID is required" && exit 1
        ;;
    *)
        echo "Unsupported provider: $PROVIDER"
        exit 1
        ;;
esac

# Debug output
if [[ "$DEBUG" == "true" ]]; then
    echo "Environment variables:"
    env | sort
    echo "Command: $COMMAND_TYPE"
    echo "Provider: $PROVIDER"
fi

# Make scripts executable
chmod +x /usr/local/bin/terraformer.sh
chmod +x /usr/local/bin/terraformer_commands.py
chmod +x /usr/local/bin/wrapper.sh

# Execute wrapper script with proper arguments
case "$COMMAND_TYPE" in
    import)
        # Store output in user's workspace
        TERRAFORM_OUTPUT_DIR="$USER_DIR/import"
        mkdir -p "$TERRAFORM_OUTPUT_DIR"
        
        exec /usr/local/bin/wrapper.sh import "$PROVIDER" \\
            "${{RESOURCE_TYPE}}" \\
            "${{RESOURCE_ID}}" \\
            "$TERRAFORM_OUTPUT_DIR" | tee >(if [[ "$PRINT_OUTPUT" == "true" ]]; then cat; fi)
        ;;
    scan)
        # Store output in user's workspace
        SCAN_OUTPUT_FILE="$USER_DIR/scan_output.${{OUTPUT_FORMAT}}"
        
        exec /usr/local/bin/wrapper.sh scan "$PROVIDER" \\
            "${{RESOURCE_TYPES}}" \\
            "${{OUTPUT_FORMAT}}" > "$SCAN_OUTPUT_FILE"
        
        if [[ "$PRINT_OUTPUT" == "true" ]]; then
            cat "$SCAN_OUTPUT_FILE"
        fi
        ;;
    *)
        echo "Unknown command type: $COMMAND_TYPE"
        exit 1
        ;;
esac
""",
                mermaid=mermaid
            )

            # Store validated config
            self._config = config

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
            parts = self._config.name.split('_')
            command_type = parts[1] if len(parts) > 1 else "scan"
            provider = parts[2] if len(parts) > 2 else "aws"

            # Generate unique workspace path
            user_email = os.environ.get('KUBIYA_USER_EMAIL', 'anonymous')
            workspace_id = str(uuid.uuid4())
            user_dir = f"/var/lib/terraform/{sanitize_email(user_email)}_{workspace_id}"

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

            # Prepare response with volume path information
            if command_type == 'import':
                output_path = f"{user_dir}/import"
            else:  # scan
                output_path = f"{user_dir}/scan_output.{kwargs.get('output_format', 'hcl')}"

            # Convert print_output to boolean for response handling
            print_output = kwargs.get('print_output', 'true').lower() == 'true'

            return {
                'success': True,
                'output': result.stdout if print_output else "Output saved to volume",
                'command': ' '.join(cmd_args),
                'output_path': output_path,
                'volume_name': "terraform_code",
                'workspace_id': workspace_id
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