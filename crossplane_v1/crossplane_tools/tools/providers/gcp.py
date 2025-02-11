"""GCP Provider Tools

This module provides tools for managing GCP resources through Crossplane.
"""
from typing import List, Dict, Any
from ..base import CrossplaneTool, Arg, Secret, get_provider_config
import logging

logger = logging.getLogger(__name__)

def create_gcp_tools() -> List[CrossplaneTool]:
    """Create and register all GCP tools."""
    tools = []
    
    try:
        # Get GCP provider configuration
        config = get_provider_config('gcp')
        if not config.get('enabled', True):
            logger.info("GCP provider is disabled in configuration")
            return tools

        # Create core GCP tools
        core_tools = {
            'gke': gcp_gke_cluster_tool,
            'sql': gcp_cloud_sql_instance_tool,
            'storage': gcp_storage_bucket_tool,
            'network': gcp_vpc_network_tool
        }

        # Add core tools if they match configuration
        for name, tool in core_tools.items():
            if config['sync_all'] or name in config['include']:
                if name not in config['exclude']:
                    tool.config.secrets = [Secret(**s) for s in config['secrets']]
                    tools.append(tool)
                    logger.info(f"Added core GCP tool: {name}")

        # Register all created tools
        CrossplaneTool.register_tools(tools)
        logger.info(f"Successfully registered {len(tools)} GCP tools")
        
    except Exception as e:
        logger.error(f"Failed to create GCP tools: {str(e)}")
    
    return tools

# Create GCP tools when module is imported
gcp_tools = create_gcp_tools()

# Export tools
__all__ = [
    'gcp_gke_cluster_tool',
    'gcp_cloud_sql_instance_tool',
    'gcp_storage_bucket_tool',
    'gcp_vpc_network_tool',
    'create_gcp_tools'
] 