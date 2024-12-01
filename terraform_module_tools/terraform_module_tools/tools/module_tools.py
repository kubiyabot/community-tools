from kubiya_sdk.tools.registry import tool_registry
from pathlib import Path
from .terraform_module_tool import TerraformModuleTool
from ..scripts.config_loader import get_module_configs

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

    # Extract source configuration
    source_config = {
        'location': config['source']['location'],
        'version': config['source'].get('version'),
        'path': config['source'].get('path'),
        'auth': config['source'].get('auth', {})
    }

    # Create module configuration
    module_config = {
        'name': config['name'],
        'description': config['description'],
        'source': source_config,
        'pre_script': config.get('pre_script')
    }

    return TerraformModuleTool(
        name=tool_name,
        description=description,
        module_config=module_config,
        action=action,
        with_pr=with_pr
    )

def initialize_module_tools():
    """Initialize all Terraform module tools."""
    tools = {}
    try:
        module_configs = get_module_configs()
        
        for module_name, config in module_configs.items():
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

    except Exception as e:
        print(f"Error initializing tools: {e}")
    
    return tools

# Initialize tools when module is imported
tools = initialize_module_tools()

# Export necessary components
__all__ = ['create_terraform_module_tool', 'tools', 'initialize_module_tools'] 