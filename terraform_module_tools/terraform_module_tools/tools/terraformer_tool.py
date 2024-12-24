from kubiya_sdk.tools import Tool, Arg, Volume
from typing import List, Dict, Any, Optional, ClassVar, TypedDict
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
import logging
from pathlib import Path
from ..scripts.error_handler import handle_script_error, ScriptError, logger
import os
import subprocess
import uuid
import re
from ..scripts.conversion_runtime import convert_former2_to_terraform

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

class ScriptConfig(TypedDict):
    main: str
    commands: Optional[str]
    wrapper: Optional[str]

class ConverterConfig(TypedDict):
    scripts: Dict[str, str]

class TerraformerTool(Tool):
    """Tool for reverse engineering existing infrastructure into Terraform code."""
    
    SUPPORTED_CONVERTERS: ClassVar[Dict[str, ConverterConfig]] = {
        'terraformer': {
            'scripts': {
                'main': 'terraformer.sh',
                'commands': 'terraformer_commands.py',
                'wrapper': 'wrapper.sh'
            }
        },
        'former2': {
            'scripts': {
                'main': 'former2.sh'
            }
        }
    }

    def __init__(self, name: str, description: str, args: List[Arg], env: List[str] = None):
        """Initialize the tool with proper base class initialization."""
        try:
            # Add base args including converter selection
            base_args = [
                Arg(
                    name="print_output",
                    description="Whether to print the generated Terraform code to stdout (true/false)",
                    type="str",
                    required=False,
                    default="true"
                ),
                Arg(
                    name="converter",
                    description="Tool to use for conversion (terraformer or former2)",
                    type="str",
                    required=False,
                    default="terraformer"
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

            # Get converter type from args or default to terraformer
            converter = next((arg.default for arg in args if arg.name == 'converter'), 'terraformer')
            
            # Get scripts for selected converter
            converter_scripts = self.SUPPORTED_CONVERTERS[converter]['scripts']
            
            # Prepare files list
            files = [
                *AWS_COMMON_FILES  # AWS config files
            ]
            
            # Add converter-specific scripts
            for script_name, script_file in converter_scripts.items():
                files.append({
                    'destination': f'/usr/local/bin/{script_file}',
                    'content': self._get_script_content(script_file)
                })

            # Generate appropriate content based on converter
            if converter == 'former2':
                content = self._generate_former2_content()
            else:  # terraformer
                content = self._generate_terraformer_content()

            # Initialize base tool
            super().__init__(
                name=config.name,
                description=config.description,
                args=config.args,
                env=config.env,
                type="docker",
                image="hashicorp/terraform:latest",
                handler=self.handle_terraform_command,
                with_files=files,
                with_volumes=[
                    Volume(
                        name="terraform_code",
                        path="/var/lib/terraform"
                    )
                ],
                content=content,
                mermaid=mermaid
            )

            # Store validated config
            self._config = config

        except Exception as e:
            logger.error(f"Failed to initialize TerraformerTool: {str(e)}")
            raise ValueError(f"Tool initialization failed: {str(e)}")

    def _generate_former2_content(self) -> str:
        """Generate content for Former2 converter."""
        return """#!/bin/bash
set -e

# Runtime workspace generation
python3 << 'EOF'
import os
import uuid
import re
from conversion_runtime import convert_former2_to_terraform

# ... (workspace generation code remains the same)
EOF

# Make scripts executable
chmod +x /usr/local/bin/former2.sh

# Execute Former2 script
/usr/local/bin/former2.sh "$COMMAND_TYPE" "$PROVIDER" "$@" | \
python3 -c "
from conversion_runtime import convert_former2_to_terraform, save_terraform_code
import sys

tf_code = convert_former2_to_terraform(sys.stdin.read())
save_terraform_code(tf_code, '$USER_DIR')

if '$PRINT_OUTPUT' == 'true':
    print(tf_code)
"
"""

    def _generate_terraformer_content(self) -> str:
        """Generate content for Terraformer converter."""
        return """#!/bin/bash
set -e

# Runtime workspace generation will happen here
python3 << 'EOF'
import os
import uuid
import re
import json
from conversion_runtime import convert_former2_to_terraform

def sanitize_email(email):
    if not email:
        return "anonymous"
    return re.sub(r'[^a-zA-Z0-9_-]', '_', email.replace('@', '_').replace('.', '_'))

user_email = os.environ.get('KUBIYA_USER_EMAIL', 'anonymous')
workspace_id = str(uuid.uuid4())
user_dir = f"/var/lib/terraform/{sanitize_email(user_email)}_{workspace_id}"

# Get converter type
converter = os.environ.get('CONVERTER', 'terraformer').lower()
command_type = os.environ.get('COMMAND_TYPE', '')
provider = os.environ.get('PROVIDER', '')

# Handle Former2 conversion if selected
if converter == 'former2' and provider == 'aws':
    try:
        # Convert Former2 output to Terraform
        former2_output = os.environ.get('FORMER2_OUTPUT', '')
        if former2_output:
            tf_code = convert_former2_to_terraform(former2_output)
            output_file = f"{user_dir}/terraform_code.tf"
            os.makedirs(user_dir, exist_ok=True)
            with open(output_file, 'w') as f:
                f.write(tf_code)
            print(f"TERRAFORM_OUTPUT_FILE={output_file}")
            print(f"CONVERSION_SUCCESS=true")
        else:
            print("CONVERSION_ERROR=No Former2 output provided")
            exit(1)
    except Exception as e:
        print(f"CONVERSION_ERROR={str(e)}")
        exit(1)

print(f"USER_DIR={user_dir}")
print(f"WORKSPACE_ID={workspace_id}")
EOF

# Read the generated variables
eval "$(python3 -c 'import os; print("TOOL_NAME=" + os.environ.get("TOOL_NAME", ""))')"
eval "$(python3 -c 'import os; print("COMMAND_TYPE=" + os.environ.get("COMMAND_TYPE", ""))')"
eval "$(python3 -c 'import os; print("PROVIDER=" + os.environ.get("PROVIDER", ""))')"

# Create the workspace directory
mkdir -p "$USER_DIR"

# Handle conversion based on selected converter
if [[ "$CONVERTER" == "former2" ]] && [[ "$PROVIDER" == "aws" ]]; then
    if [[ -n "$CONVERSION_ERROR" ]]; then
        echo "Error converting Former2 output: $CONVERSION_ERROR"
        exit 1
    fi
    
    if [[ "$PRINT_OUTPUT" == "true" ]] && [[ -f "$TERRAFORM_OUTPUT_FILE" ]]; then
        cat "$TERRAFORM_OUTPUT_FILE"
    fi
else
    # ... (existing terraformer logic remains the same)
fi"""

    def _get_script_content(self, script_name: str) -> str:
        """Get the content of a script file."""
        try:
            script_path = Path(__file__).parent.parent / 'scripts' / script_name
            with open(script_path, 'r') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to read script {script_name}: {str(e)}")
            raise ValueError(f"Failed to read script {script_name}")

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

            # Handle Former2 conversion if selected
            converter = kwargs.get('converter', 'terraformer').lower()
            if converter == 'former2':
                if provider != 'aws':
                    raise ValueError("Former2 conversion is only supported for AWS")
                
                former2_output = kwargs.get('former2_output')
                if not former2_output:
                    raise ValueError("Former2 output is required when using Former2 converter")
                
                env['FORMER2_OUTPUT'] = former2_output

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