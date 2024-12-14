import logging
from typing import List
from kubiya_sdk.tools.registry import tool_registry
from .terraform_module_tool import TerraformModuleTool
from ..parser import TerraformModuleParser

logger = logging.getLogger(__name__)

def parse_module_urls(urls_str: str) -> List[str]:
    """Parse comma-separated module URLs string."""
    if not urls_str:
        return []
    return [url.strip() for url in urls_str.split(',') if url.strip()]

def create_terraform_module_tool(module_url: str, action: str, with_pr: bool = False):
    """Create a Terraform module tool from URL."""
    try:
        # Parse module information from URL
        parser = TerraformModuleParser(source_url=module_url)
        variables, warnings, errors = parser.get_variables()
        
        if errors:
            logger.error(f"Failed to parse module {module_url}: {errors}")
            return None
            
        for warning in warnings:
            logger.warning(f"Warning for {module_url}: {warning}")

        # Extract module name from URL
        module_name = module_url.split('/')[-1].replace('.git', '')
        
        # Create module configuration
        module_config = {
            'name': module_name,
            'description': f"Terraform module from {module_url}",
            'source': {
                'location': module_url,
                'version': 'master'  # Default to master, can be made configurable
            }
        }

        # Generate tool name
        action_suffix = f"_{action}"
        if action == 'plan' and with_pr:
            action_suffix = '_plan_pr'
        tool_name = f"tf_{module_name.lower().replace('-', '_')}{action_suffix}"

        return TerraformModuleTool(
            name=tool_name,
            description=f"Manage {module_name} infrastructure",
            module_config=module_config,
            action=action,
            with_pr=with_pr
        )

    except Exception as e:
        logger.error(f"Failed to create tool for {module_url}: {str(e)}")
        return None

def initialize_tools():
    """Initialize all Terraform module tools from dynamic configuration."""
    tools = []
    try:
        # Get dynamic configuration from tool registry
        config = tool_registry.dynamic_config
        if not config:
            logger.warning("No dynamic configuration provided")
            raise Exception("No dynamic configuration provided - please provide a comma separated list of Terraform module URLs to initialize the tools for")

        # Get module URLs from configuration
        module_urls = parse_module_urls(config.get('tf_modules_urls', ''))
        if not module_urls:
            logger.warning("No Terraform module URLs provided in configuration")
            raise Exception("No Terraform module URLs provided in configuration - please provide tf_modules_urls")

        logger.info(f"Found {len(module_urls)} module URLs in configuration")

        # Create tools for each module
        for module_url in module_urls:
            try:
                logger.info(f"Creating tools for module: {module_url}")
                
                # Create and register tools
                created_tools = []
                
                if plan_tool := create_terraform_module_tool(module_url, 'plan'):
                    created_tools.append(plan_tool)
                    tool_registry.register("terraform", plan_tool)

                if plan_pr_tool := create_terraform_module_tool(module_url, 'plan', with_pr=True):
                    created_tools.append(plan_pr_tool)
                    tool_registry.register("terraform", plan_pr_tool)

                if apply_tool := create_terraform_module_tool(module_url, 'apply'):
                    created_tools.append(apply_tool)
                    tool_registry.register("terraform", apply_tool)

                if created_tools:
                    tools.extend(created_tools)
                    logger.info(f"Successfully created {len(created_tools)} tools for module: {module_url}")
                else:
                    logger.warning(f"No tools were created for module: {module_url}")
                
            except Exception as e:
                logger.error(f"Failed to create tools for module {module_url}: {str(e)}")
                continue

        if not tools:
            logger.warning("No tools were created from any modules")
            return []

        logger.info(f"Successfully created {len(tools)} tools total")
        return tools
        
    except Exception as e:
        logger.error(f"Failed to initialize tools: {str(e)}")
        raise

__all__ = ['initialize_tools', 'create_terraform_module_tool']