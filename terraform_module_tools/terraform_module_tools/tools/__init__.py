import logging
from typing import List
from kubiya_sdk.tools.registry import tool_registry
from .terraform_module_tool import TerraformModuleTool
from ..parser import TerraformModuleParser
import re

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

        # Extract clean module name from URL
        module_name = _get_clean_module_name(module_url)
        
        # Create module configuration
        module_config = {
            'name': module_name,
            'description': f"Terraform module for {module_name}",
            'source': {
                'location': module_url,
                'version': parser.source.get_ref() or 'latest'
            }
        }

        # Generate tool name
        action_suffix = '_plan_pr' if action == 'plan' and with_pr else f'_{action}'
        tool_name = f"tf_{module_name}{action_suffix}"

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

def _get_clean_module_name(url: str) -> str:
    """Extract a clean module name from the URL."""
    # Remove any /tree/<branch> parts
    if '/tree/' in url:
        url = url.split('/tree/')[0]
    
    # Handle different URL formats
    if url.startswith(('http://', 'https://', 'git@')):
        # GitHub/GitLab URLs
        if 'github.com' in url or 'gitlab.com' in url:
            # Extract the repo name from the URL
            parts = url.rstrip('/').rstrip('.git').split('/')
            repo_name = parts[-1]
            
            # Handle terraform-provider-name format
            if repo_name.startswith('terraform-'):
                # Extract the actual resource name
                name_parts = repo_name.split('-')
                if len(name_parts) >= 3:
                    # terraform-aws-vpc -> aws_vpc
                    provider = name_parts[1]
                    resource = '_'.join(name_parts[2:])
                    return f"{provider}_{resource}"
            
            return repo_name.replace('-', '_')
            
    elif url.count('/') == 2:  # registry format (e.g., "hashicorp/consul/aws")
        # Extract the module name from registry format
        namespace, name, provider = url.split('/')
        return f"{provider}_{name}"
    
    # Fallback: clean up whatever we have
    name = url.split('/')[-1].replace('-', '_')
    name = re.sub(r'[^\w_]', '', name)  # Remove any non-word chars except underscore
    return name.lower()

def initialize_tools():
    """Initialize all Terraform module tools from dynamic configuration."""
    tools = []
    try:
        # Get dynamic configuration from tool registry
        config = tool_registry.dynamic_config
        if not config:
            error_msg = "No dynamic configuration provided - please provide a comma separated list of Terraform module URLs to initialize the tools for"
            logger.error(error_msg)
            raise ValueError(error_msg)

        # Get module URLs from configuration
        module_urls = parse_module_urls(config.get('tf_modules_urls', ''))
        if not module_urls:
            error_msg = "No Terraform module URLs provided in configuration - please provide tf_modules_urls"
            logger.error(error_msg)
            raise ValueError(error_msg)

        logger.info(f"Found {len(module_urls)} module URLs in configuration")

        # Create tools for each module
        for module_url in module_urls:
            try:
                logger.info(f"Creating tools for module: {module_url}")
                
                # Create and register tools
                created_tools = []
                
                for action in ['plan', 'plan_pr', 'apply']:
                    with_pr = action == 'plan_pr'
                    base_action = 'plan' if with_pr else action
                    
                    tool = create_terraform_module_tool(module_url, base_action, with_pr)
                    if tool:
                        created_tools.append(tool)
                        tool_registry.register("terraform", tool)
                        logger.info(f"Created {action} tool for {module_url}")

                if created_tools:
                    tools.extend(created_tools)
                    logger.info(f"Successfully created {len(created_tools)} tools for module: {module_url}")
                else:
                    error_msg = f"Failed to create any tools for module: {module_url}"
                    logger.error(error_msg)
                    raise ValueError(error_msg)
                
            except Exception as e:
                error_msg = f"Failed to create tools for module {module_url}: {str(e)}"
                logger.error(error_msg)
                raise ValueError(error_msg)

        if not tools:
            error_msg = "No tools were created from any modules"
            logger.error(error_msg)
            raise ValueError(error_msg)

        logger.info(f"Successfully created {len(tools)} tools total")
        return tools
        
    except Exception as e:
        logger.error(f"Failed to initialize tools: {str(e)}")
        raise

__all__ = ['initialize_tools', 'create_terraform_module_tool']