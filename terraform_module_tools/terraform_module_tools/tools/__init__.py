import logging
from .terraform_module_tool import TerraformModuleTool
from ..scripts.config_loader import get_module_configs
from kubiya_sdk.tools.registry import tool_registry

logger = logging.getLogger(__name__)

def create_terraform_module_tool(config: dict, action: str, with_pr: bool = False):
    """Create a Terraform module tool from configuration."""
    
    # Generate tool name
    action_suffix = f"_{action}"
    if action == 'plan' and with_pr:
        action_suffix = '_plan_pr'
    tool_name = f"tf_{config['name'].lower().replace(' ', '_')}{action_suffix}"
    
    # Create tool description
    action_desc = {
        'plan': 'Plan changes for',
        'plan_pr': 'Plan changes and create PR for',
        'apply': 'Apply changes to'
    }
    description = f"{action_desc.get(action, 'Manage')} {config['description']}"

    # Create module configuration
    module_config = {
        'name': config['name'],
        'description': config['description'],
        'source': config['source'],  # Pass the entire source object
        'pre_script': config.get('pre_script')
    }

    return TerraformModuleTool(
        name=tool_name,
        description=description,
        module_config=module_config,
        action=action,
        with_pr=with_pr
    )

def initialize_tools():
    """Initialize and register all Terraform module tools."""
    tools = {}
    try:
        logger.info("Initializing Terraform module tools...")
        module_configs = get_module_configs()
        
        for module_name, config in module_configs.items():
            try:
                logger.info(f"Creating tools for module: {module_name}")
                
                # Create plan tool
                plan_tool = create_terraform_module_tool(config, 'plan')
                tools[plan_tool.name] = plan_tool
                tool_registry.register("terraform", plan_tool)

                # Create plan with PR tool
                plan_pr_tool = create_terraform_module_tool(config, 'plan', with_pr=True)
                tools[plan_pr_tool.name] = plan_pr_tool
                tool_registry.register("terraform", plan_pr_tool)

                # Create apply tool
                apply_tool = create_terraform_module_tool(config, 'apply')
                tools[apply_tool.name] = apply_tool
                tool_registry.register("terraform", apply_tool)
                
                logger.info(f"Successfully created tools for module: {module_name}")
                
            except Exception as e:
                logger.error(f"Failed to create tools for module {module_name}: {str(e)}")
                continue

        return list(tools.values())
        
    except Exception as e:
        logger.error(f"Failed to initialize tools: {str(e)}")
        raise

__all__ = ['initialize_tools', 'create_terraform_module_tool', 'TerraformModuleTool']