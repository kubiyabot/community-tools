"""AWS Provider Tools

This module provides tools for managing AWS resources through Crossplane.
"""
from typing import List, Dict, Any
from ..base import CrossplaneTool, Arg, Secret, get_provider_config
import logging

logger = logging.getLogger(__name__)

def create_aws_tools() -> List[CrossplaneTool]:
    """Create and register all AWS tools."""
    tools = []
    
    try:
        # Get AWS provider configuration
        config = get_provider_config('aws')
        if not config.get('enabled', True):
            logger.info("AWS provider is disabled in configuration")
            return tools

        # Create core AWS tools
        core_tools = {
            's3': aws_s3_bucket_tool,
            'eks': aws_eks_cluster_tool,
            'rds': aws_rds_instance_tool,
            'vpc': aws_vpc_tool
        }

        # Add core tools if they match configuration
        for name, tool in core_tools.items():
            if config['sync_all'] or name in config['include']:
                if name not in config['exclude']:
                    tool.config.secrets = [Secret(**s) for s in config['secrets']]
                    tools.append(tool)
                    logger.info(f"Added core AWS tool: {name}")

        # Register all created tools
        CrossplaneTool.register_tools(tools)
        logger.info(f"Successfully registered {len(tools)} AWS tools")
        
    except Exception as e:
        logger.error(f"Failed to create AWS tools: {str(e)}")
    
    return tools

# Create AWS tools when module is imported
aws_tools = create_aws_tools()

# Export tools
__all__ = [
    'aws_s3_bucket_tool',
    'aws_eks_cluster_tool',
    'aws_rds_instance_tool',
    'aws_vpc_tool',
    'create_aws_tools'
] 