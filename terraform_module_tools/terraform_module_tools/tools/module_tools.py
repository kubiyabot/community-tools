from kubiya_sdk.tools.registry import tool_registry
from pathlib import Path
from typing import Dict, Any, Optional, List
from .terraform_module_tool import TerraformModuleTool
from ..scripts.config_loader import get_module_configs, ConfigurationError
import logging
from kubiya_sdk.tools.tool import Tool, Arg

logger = logging.getLogger(__name__)

def create_terraform_module_tool(name: str, description: str, args: List[Arg], env: List[str] = None) -> Tool:
    """Create a Terraform module tool with proper configuration."""
    mermaid = {
        'graph': """
            graph TD
                A[Start] --> B[Load Module]
                B --> C[Validate Variables]
                C --> D[Apply Configuration]
                D --> E[Execute Module]
                E --> F[End]
        """
    }
    
    return Tool(
        name=name,
        description=description,
        args=args,
        env=env or [],
        type="docker",
        image="hashicorp/terraform:latest",
        handler=handle_terraform_module,
        mermaid=mermaid
    )

def initialize_module_tools(config: Optional[Dict[str, Any]] = None):
    """Initialize all Terraform module tools."""
    tools = {}
    try:
        if config is None:
            # Get dynamic configuration from tool registry
            config = getattr(tool_registry, 'dynamic_config', {})
            if not config:
                logger.warning("No configuration found")
                return tools

        # Get module configurations
        try:
            module_configs = get_module_configs(config)
        except ConfigurationError as e:
            logger.error(f"Failed to get module configurations: {str(e)}")
            return tools

        if not module_configs:
            logger.warning("No module configurations found")
            return tools

        logger.info(f"Initializing {len(module_configs)} module(s)")
        
        for module_name, config in module_configs.items():
            try:
                # Create plan tool
                plan_tool = create_terraform_module_tool(config, 'plan')
                if plan_tool:
                    tools[plan_tool.name] = plan_tool
                    tool_registry.register("terraform", plan_tool)
                    logger.info(f"Created plan tool for {module_name}")

                # Create plan with PR tool
                plan_pr_tool = create_terraform_module_tool(config, 'plan', with_pr=True)
                if plan_pr_tool:
                    tools[plan_pr_tool.name] = plan_pr_tool
                    tool_registry.register("terraform", plan_pr_tool)
                    logger.info(f"Created plan PR tool for {module_name}")

                # Create apply tool
                apply_tool = create_terraform_module_tool(config, 'apply')
                if apply_tool:
                    tools[apply_tool.name] = apply_tool
                    tool_registry.register("terraform", apply_tool)
                    logger.info(f"Created apply tool for {module_name}")

            except Exception as e:
                logger.error(f"Failed to create tools for module {module_name}: {str(e)}")
                continue

    except Exception as e:
        logger.error(f"Error initializing tools: {str(e)}")
    
    return tools

# Don't initialize tools on import anymore
tools = {}

# No __all__ needed here 