from kubiya_sdk.tools import Tool, Arg, FileSpec
from typing import List, Dict, Any, Optional
import os
import json
import logging
from pathlib import Path
from ..parser import TerraformModuleParser
from pydantic import Field, root_validator
from .terraform_module_tool import TerraformModuleTool

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

MAX_DESCRIPTION_LENGTH = 1024

def create_terraform_module_tool(
    name: str,
    module_config: Dict[str, Any],
    action: str = 'plan',
    with_pr: bool = False,
    env: Optional[List[str]] = None,
    secrets: Optional[List[str]] = None
) -> Tool:
    """Create a Terraform module tool."""
    return TerraformModuleTool(
        name=name,
        module_config=module_config,
        action=action,
        with_pr=with_pr,
        env=env or [],
        secrets=secrets or []
    )

def initialize_module_tools(config: Dict[str, Any]) -> Dict[str, Tool]:
    """Initialize all module tools from configuration."""
    tools = {}
    
    if not config.get('terraform', {}).get('modules'):
        logger.info("No module configuration found")
        return tools

    for module_name, module_config in config['terraform']['modules'].items():
        try:
            # Create plan tool
            plan_tool = create_terraform_module_tool(
                name=f"terraform_plan_{module_name}",
                module_config=module_config,
                action='plan'
            )
            tools[f"plan_{module_name}"] = plan_tool
            logger.info(f"Created plan tool for module {module_name}")

            # Create apply tool
            apply_tool = create_terraform_module_tool(
                name=f"terraform_apply_{module_name}",
                module_config=module_config,
                action='apply'
            )
            tools[f"apply_{module_name}"] = apply_tool
            logger.info(f"Created apply tool for module {module_name}")

            # Create plan with PR tool if enabled
            if module_config.get('enable_pr', False):
                pr_tool = create_terraform_module_tool(
                    name=f"terraform_plan_pr_{module_name}",
                    module_config=module_config,
                    action='plan',
                    with_pr=True
                )
                tools[f"plan_pr_{module_name}"] = pr_tool
                logger.info(f"Created plan with PR tool for module {module_name}")

        except Exception as e:
            logger.error(f"Failed to create tools for module {module_name}: {str(e)}")
            continue

    return tools

__all__ = ['create_terraform_module_tool', 'initialize_module_tools'] 