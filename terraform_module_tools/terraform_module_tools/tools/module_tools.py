from kubiya_sdk.tools import Tool, Arg
from kubiya_sdk.tools.registry import tool_registry
from pathlib import Path
from typing import Dict, Any, Optional, List
from .terraform_module_tool import TerraformModuleTool
from ..scripts.config_loader import get_module_configs, ConfigurationError
from ..scripts.error_handler import handle_script_error, ScriptError, logger
import logging

logger = logging.getLogger(__name__)

@handle_script_error
def create_terraform_module_tool(config: dict, action: str, with_pr: bool = False):
    """Create a Terraform module tool from configuration."""
    try:
        # Generate tool name
        action_suffix = f"_{action}"
        if action == 'plan' and with_pr:
            action_suffix = '_plan_pr'
        base_name = config['name'].lower().replace(' ', '_')[:30]
        tool_name = f"tf_self_service_{base_name}{action_suffix}"

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
            'source': config['source'],
            'pre_script': config.get('pre_script')
        }
        
        # Add mermaid diagram
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
        
        return TerraformModuleTool(
            name=tool_name,
            description=description,
            module_config=module_config,
            action=action,
            with_pr=with_pr,
            mermaid=mermaid
        )
    except Exception as e:
        logger.error(f"Failed to create terraform module tool: {str(e)}")
        raise ScriptError(str(e))

def initialize_module_tools(config: Optional[Dict[str, Any]] = None) -> Dict[str, Tool]:
    """Initialize all Terraform module tools."""
    tools = {}
    try:
        if config is None:
            config = getattr(tool_registry, 'dynamic_config', {})
            if not config:
                logger.warning("No configuration found")
                return tools

        module_configs = get_module_configs(config)
        if not module_configs:
            logger.warning("No module configurations found")
            return tools

        logger.info(f"Initializing {len(module_configs)} module(s)")
        
        for module_name, module_config in module_configs.items():
            try:
                # Create plan tool
                plan_tool = create_terraform_module_tool(module_config, 'plan')
                if plan_tool:
                    tools[plan_tool.name] = plan_tool
                    tool_registry.register("terraform", plan_tool)
                    logger.info(f"Created plan tool for {module_name}")

                # Create plan with PR tool
                plan_pr_tool = create_terraform_module_tool(module_config, 'plan', with_pr=True)
                if plan_pr_tool:
                    tools[plan_pr_tool.name] = plan_pr_tool
                    tool_registry.register("terraform", plan_pr_tool)
                    logger.info(f"Created plan PR tool for {module_name}")

                # Create apply tool
                apply_tool = create_terraform_module_tool(module_config, 'apply')
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

__all__ = ['create_terraform_module_tool', 'initialize_module_tools'] 