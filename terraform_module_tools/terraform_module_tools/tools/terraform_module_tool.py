from kubiya_sdk.tools import Tool, Arg, FileSpec
from typing import Dict, Any, List, Optional
from pydantic import root_validator, Field
import logging
import json
from pathlib import Path

logger = logging.getLogger(__name__)

class TerraformModuleTool(Tool):
    """Base class for Terraform module tools."""
    module_config: Dict[str, Any]
    action: str = 'plan'
    with_pr: bool = False
    env: List[str] = Field(default_factory=list)
    secrets: List[str] = Field(default_factory=list)
    with_files: List[FileSpec] = Field(default_factory=list)

    @root_validator(pre=True)
    def initialize_tool(cls, values):
        """Initialize the tool with proper schema validation."""
        try:
            # Validate module config
            if not isinstance(values['module_config'], dict):
                raise ValueError("module_config must be a dictionary")
            
            required_fields = ['name', 'description', 'source']
            for field in required_fields:
                if field not in values['module_config']:
                    raise ValueError(f"module_config missing required field: {field}")
                
            if not isinstance(values['module_config']['source'], dict):
                raise ValueError("module_config['source'] must be a dictionary")
                
            if 'location' not in values['module_config']['source']:
                raise ValueError("module_config['source'] missing required field: location")

            # Create base args
            args = [
                Arg(
                    name="variables",
                    description="Variables for the Terraform module",
                    type="dict",
                    required=False,
                    default="{}"
                )
            ]

            # Create mermaid diagram if not provided
            if not values['mermaid']:
                values['mermaid'] = {
                    'graph': f"""
                        graph TD
                            A[Start] --> B[Load {values['action'].title()} Configuration]
                            B --> C[Validate Variables]
                            C --> D[Execute {values['action'].title()}]
                            D --> E[Process Results]
                            E --> F[End]
                    """
                }

            # Create action description
            action_desc = {
                'plan': 'Plan infrastructure changes for',
                'apply': 'Apply infrastructure changes to',
                'plan_pr': 'Plan infrastructure changes and create PR for'
            }
            
            current_action = 'plan_pr' if values['action'] == 'plan' and values['with_pr'] else values['action']
            
            tool_description = (
                f"{action_desc[current_action]} {values['module_config']['description']} "
                f"(source: {values['module_config']['source']['location']}) - "
                f"version: {values['module_config']['source'].get('version', 'latest')}"
            )

            # Prepare script files
            scripts_dir = Path(__file__).parent.parent / 'scripts'
            required_files = {
                'terraform_plan.py',
                'terraform_apply.py',
                'prepare_tfvars.py',
                'terraform_handler.py',
                'get_module_vars.py',
                'error_handler.py',
                'configs/module_configs.json',
                'requirements.txt'
            }

            # Create FileSpec objects for all required files
            with_files = []
            for filename in required_files:
                file_path = scripts_dir / filename
                if file_path.exists():
                    dest_path = f"/opt/scripts/{filename}"
                    with_files.append(FileSpec(
                        destination=dest_path,
                        content=file_path.read_text()
                    ))
                else:
                    logger.warning(f"Required script file not found: {filename}")

            # Add module variables and config files
            with_files.extend([
                FileSpec(
                    destination="/opt/module_variables.json",
                    content=json.dumps(values['variables'], indent=2)
                ),
                FileSpec(
                    destination="/opt/scripts/.module_config.json",
                    content=json.dumps(values['module_config'])
                )
            ])

            # Update values with files and other configurations
            values.update({
                'with_files': with_files,
                'type': "docker",
                'image': "python:3.9-alpine",
                'env': values['env'] + ["KUBIYA_USER_EMAIL"],
                'secrets': values['secrets'] + ["GH_TOKEN"],
                'content': cls._generate_script_content(values),
                'mermaid': cls._generate_mermaid_diagram()
            })

            # Initialize base tool
            super().__init__(
                name=values['name'],
                description=tool_description,
                args=args,
                env=values['env'],
                secrets=values['secrets'],
                type=values['type'],
                image=values['image'],
                handler=cls.handle_terraform_module,
                mermaid=values['mermaid']
            )

            # Store module-specific configurations
            cls.module_config = values['module_config']
            cls.action = values['action']
            cls.with_pr = values['with_pr']

        except Exception as e:
            logger.error(f"Failed to initialize TerraformModuleTool: {str(e)}")
            raise ValueError(f"Tool initialization failed: {str(e)}")

        return values

    @classmethod
    def _generate_script_content(cls, values: Dict[str, Any]) -> str:
        """Generate the script content for the tool."""
        # ... (implementation of script content generation)

    @classmethod
    def _generate_mermaid_diagram(cls) -> str:
        """Generate the mermaid diagram for the tool."""
        # ... (implementation of mermaid diagram generation)

    async def handle_terraform_module(self, **kwargs) -> Dict[str, Any]:
        """Handle Terraform module operations."""
        try:
            # Basic validation
            if not self.module_config:
                raise ValueError("No module configuration available")

            # Process variables
            variables = kwargs.get('variables', {})
            if isinstance(variables, str):
                try:
                    variables = json.loads(variables)
                except json.JSONDecodeError:
                    raise ValueError("Invalid JSON in variables parameter")

            # Return basic success response for now
            return {
                'success': True,
                'action': self.action,
                'module': self.module_config['name'],
                'variables': variables
            }

        except Exception as e:
            logger.error(f"Failed to handle terraform module: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    class Config:
        arbitrary_types_allowed = True
