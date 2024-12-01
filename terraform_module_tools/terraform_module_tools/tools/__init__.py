import logging
from kubiya_sdk.tools.registry import tool_registry
from .module_tools import create_terraform_module_tool, MODULE_CONFIGS

logger = logging.getLogger(__name__)

# Initialize tools dictionary at module level
tools = {}

def initialize_tools():
    """Initialize and register all Terraform module tools."""
    try:
        logger.info("Initializing Terraform module tools...")
        
        # Create and register tools for each module configuration
        for module_name, config in MODULE_CONFIGS.items():
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

        return list(tools.values())
        
    except Exception as e:
        logger.error(f"Failed to initialize tools: {str(e)}")
        raise

__all__ = ['initialize_tools', 'create_terraform_module_tool', 'tools']