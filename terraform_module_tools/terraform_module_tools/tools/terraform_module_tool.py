from kubiya_sdk.tools import Tool, Arg, FileSpec
from typing import List, Dict, Any, Optional
import logging
from pathlib import Path
from ..parser import TerraformModuleParser
from pydantic import BaseModel, Field
import json

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

MAX_DESCRIPTION_LENGTH = 1024

def map_terraform_type_to_arg_type(tf_type: str) -> str:
    """Map Terraform types to Kubiya SDK Arg types."""
    base_type = tf_type.lower().strip()

    if base_type == 'bool':
        return 'bool'
    elif base_type in ['number', 'int', 'float']:
        return 'int'
    elif base_type in ['string']:
        return 'str'
    elif base_type.startswith('list(') or base_type.startswith('set('):
        return 'list'
    elif base_type.startswith('map(') or base_type == 'map':
        return 'dict'
    elif base_type == 'any':
        return 'str'  # Default to str for 'any' type
    else:
        # Default to str for complex or unknown types
        return 'str'

def format_description(description: str, var_type: str, example: str) -> str:
    """Format description with type information and example."""
    formatted = description if description else "No description provided"

    base_type = var_type.lower().strip()

    if base_type.startswith('list(') or base_type.startswith('set('):
        formatted += f"\n\nExpects a JSON array. Example:\n```json\n{example}\n```"
    elif base_type.startswith('map(') or base_type == 'map':
        formatted += f"\n\nExpects a JSON object. Example:\n```json\n{example}\n```"
    elif base_type == 'bool':
        formatted += f"\n\nExpects a boolean value (`true` or `false`). Example: `{example}`"
    elif base_type in ['number', 'int', 'float']:
        formatted += f"\n\nExpects a numeric value. Example: `{example}`"
    else:
        formatted += f"\n\nExample: `{example}`"

    # Truncate if too long
    if len(formatted) > MAX_DESCRIPTION_LENGTH:
        return formatted[:MAX_DESCRIPTION_LENGTH - 3] + "..."
    return formatted

class TerraformModuleTool(Tool):
    """Base class for Terraform module tools."""

    module_config: Dict[str, Any] = Field(...)
    action: str = 'plan'
    with_pr: bool = False
    env: List[str] = Field(default_factory=list)
    secrets: List[str] = Field(default_factory=list)
    mermaid: Optional[str] = None

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, **data):
        super().__init__(**data)
        logger.info(f"Creating tool for module: {self.name}")

        if not self.module_config.get('source', {}).get('location'):
            raise ValueError(f"Module {self.name} is missing source location")

        # Auto-discover variables
        try:
            logger.info(f"Discovering variables from: {self.module_config['source']['location']}")
            parser = TerraformModuleParser(
                source_url=self.module_config['source']['location'],
                ref=self.module_config['source'].get('version'),
                path=self.module_config['source'].get('path')
            )
            variables, warnings, errors = parser.get_variables()

            if errors:
                for error in errors:
                    logger.error(f"Variable discovery error: {error}")
                raise ValueError(f"Failed to discover variables: {errors[0]}")

            for warning in warnings:
                logger.warning(f"Variable discovery warning: {warning}")

            if not variables:
                raise ValueError(f"No variables found in module {self.name}")

            logger.info(f"Found {len(variables)} variables")

        except Exception as e:
            logger.error(f"Failed to auto-discover variables: {str(e)}", exc_info=True)
            raise ValueError(f"Variable discovery failed: {str(e)}")

        # Convert variables to args list
        args = []
        for var_name, var_config in variables.items():
            try:
                # Get the cleaned and normalized type
                var_type = var_config['type']

                # Map to supported type
                arg_type = map_terraform_type_to_arg_type(var_type)
                logger.debug(f"Mapping variable {var_name} of type {var_type} to {arg_type}")

                # Format description with type info and example
                description = format_description(
                    var_config.get('description', ''),
                    var_type,
                    var_config['example']
                )

                # Create Arg object
                arg = Arg(
                    name=var_name,
                    description=description,
                    type=arg_type,
                    required=var_config.get('required', False),
                    default=None  # We will set default below if available
                )

                # Add default if present
                if 'default' in var_config and var_config['default'] is not None:
                    if arg_type in ['str']:
                        arg.default = str(var_config['default'])
                    elif arg_type in ['int']:
                        try:
                            arg.default = int(var_config['default'])
                        except (ValueError, TypeError):
                            logger.warning(f"Could not convert default value for {var_name} to int")
                    elif arg_type == 'bool':
                        arg.default = bool(var_config['default'])
                    elif arg_type in ['list', 'dict']:
                        arg.default = json.loads(var_config['default']) if isinstance(var_config['default'], str) else var_config['default']

                args.append(arg)
                logger.info(f"Added argument: {var_name} ({arg_type})")

            except Exception as e:
                logger.error(f"Failed to process variable {var_name}: {str(e)}", exc_info=True)
                raise ValueError(f"Failed to process variable {var_name}: {str(e)}")

        if not args:
            raise ValueError(f"No valid arguments created for module {self.name}")

        # Prepare script content
        script_name = 'plan_with_pr.py' if self.action == 'plan' and self.with_pr else f'{self.action}.py'
        pre_script = self.module_config.get('pre_script', '')
        if pre_script:
            pre_script = (
                f"\n# Run pre-script\n"
                f"cat > /tmp/pre_script.sh << 'EOF'\n{pre_script}\nEOF\n"
                f"chmod +x /tmp/pre_script.sh\n"
                f"/tmp/pre_script.sh || exit 1\n"
            )

        content = f"""
# Install required packages
pip install -q slack_sdk requests

# Download hcl2json if needed
if ! command -v hcl2json &> /dev/null; then
    curl -L -o /usr/local/bin/hcl2json https://github.com/tmccombs/hcl2json/releases/download/v0.6.4/hcl2json_linux_amd64
    chmod +x /usr/local/bin/hcl2json
fi
{pre_script}
# Run Terraform {self.action}
python /opt/scripts/{script_name} '{{{{ .module_config | toJson }}}}' '{{{{ .variables | toJson }}}}' || exit 1
"""

        # Set additional attributes
        self.type = "docker"
        self.image = "hashicorp/terraform:latest"
        self.content = content
        self.icon_url = "https://user-images.githubusercontent.com/31406378/108641411-f9374f00-7496-11eb-82a7-0fa2a9cc5f93.png"
        self.args = args

        # Append common environment variables and secrets
        self.env = (self.env or []) + [
            "SLACK_CHANNEL_ID",
            "SLACK_THREAD_TS",
            "GIT_TOKEN",
        ]

        self.secrets = (self.secrets or []) + [
            "SLACK_API_TOKEN",
        ]

        # Get script files
        script_files = {}
        scripts_dir = Path(__file__).parent.parent / 'scripts'
        for script_file in scripts_dir.glob('*.py'):
            if script_file.name.endswith('.py'):
                script_files[script_file.name] = script_file.read_text()

        if not script_files:
            raise ValueError("No script files found")

        self.with_files = [
            FileSpec(
                destination=f"/opt/scripts/{script_name}",
                content=script_content
            )
            for script_name, script_content in script_files.items()
        ]

        # Generate dynamic mermaid diagram
        self.mermaid = self._generate_mermaid_diagram()

    def _generate_mermaid_diagram(self) -> str:
        """Generate a dynamic mermaid diagram based on the tool's parameters."""
        module_name = self.module_config['name']
        action_display = "Plan" if self.action == 'plan' else "Apply"

        participants = [
            'participant U as 👤 User',
            'participant B as 🤖 Bot',
            'participant T as 🏗️ Terraform',
        ]
        if self.with_pr:
            participants.append('participant G as 📦 Git/PR')

        diagram_steps = [
            'Note over U,B: 🚀 Terraform Self-Service Flow',
            f'U->>B: 💬 Requests to **{action_display}** *{module_name}*',
            'B-->>T: Prepares Terraform operation',
            f'T-->>B: **{action_display}** ready',
        ]

        if self.with_pr:
            diagram_steps.extend([
                'B->>G: Creates Pull Request',
                'G-->>B: PR Created',
                'B-->>U: 🎉 PR Ready for Review!',
            ])
        else:
            diagram_steps.append('B-->>U: 🎉 Operation Completed Successfully!')

        diagram = '\n'.join(participants + diagram_steps)

        mermaid_diagram = f'sequenceDiagram\n{diagram}'
        return mermaid_diagram