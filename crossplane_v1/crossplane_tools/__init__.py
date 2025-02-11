"""Crossplane Tools Package

This package provides tools for managing Crossplane installations and resources.
"""
import os
import sys
import logging
from kubiya_sdk.tools.registry import tool_registry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def initialize():
    """Initialize Crossplane tools."""
    try:
        logger.info("Starting Crossplane tools initialization...")
        
        # Import core tools
        logger.info("Loading core tools...")
        from .tools.core import (
            install_crossplane_tool,
            uninstall_crossplane_tool,
            get_status_tool,
            version_tool,
            debug_mode_tool
        )
        
        # Import provider management tools
        logger.info("Loading provider management tools...")
        from .tools.providers import (
            install_provider_tool,
            configure_provider_tool,
            list_providers_tool,
            get_provider_status_tool,
            uninstall_provider_tool,
            apply_provider_resource_tool
        )
        
        # Import provider-specific tools
        logger.info("Loading provider-specific tools...")
        try:
            # AWS Provider tools
            from .tools.providers.aws import (
                aws_s3_bucket_tool,
                aws_eks_cluster_tool,
                aws_rds_instance_tool,
                aws_vpc_tool
            )
            logger.info("✅ AWS provider tools loaded")
        except Exception as e:
            logger.warning(f"Failed to load AWS provider tools: {str(e)}")

        try:
            # GCP Provider tools
            from .tools.providers.gcp import (
                gcp_gke_cluster_tool,
                gcp_storage_bucket_tool,
                gcp_sql_instance_tool,
                gcp_vpc_network_tool
            )
            logger.info("✅ GCP provider tools loaded")
        except Exception as e:
            logger.warning(f"Failed to load GCP provider tools: {str(e)}")

        try:
            # Documentation tools
            from .tools.providers.docs import (
                generate_provider_docs_tool,
                view_provider_docs_tool,
                export_provider_docs_tool
            )
            logger.info("✅ Documentation tools loaded")
        except Exception as e:
            logger.warning(f"Failed to load documentation tools: {str(e)}")
        
        # Set version if available
        version = os.getenv('KUBIYA_VERSION', 'development')
        logger.info(f"Running version: {version}")
        
        logger.info("Crossplane tools initialization completed successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize Crossplane tools: {str(e)}")
        raise

# Run initialization when module is imported
logger.info("Loading Crossplane tools module...")
initialize()

__version__ = "0.1.0" 