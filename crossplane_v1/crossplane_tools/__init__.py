"""Crossplane Tools Package

This package provides tools for managing Crossplane installations and resources.
"""
import os
import logging

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
        
        # Import and initialize core tools
        logger.info("Loading core tools...")
        from .tools.core import create_core_tools
        core_tools = create_core_tools()
        logger.info(f"✅ Loaded {len(core_tools)} core tools")
        
        # Import and initialize provider management tools
        logger.info("Loading provider management tools...")
        from .tools.providers import create_provider_tools
        provider_tools = create_provider_tools()
        logger.info(f"✅ Loaded {len(provider_tools)} provider management tools")
        
        # Import and initialize AWS provider tools
        logger.info("Loading AWS provider tools...")
        try:
            from .tools.providers.aws import create_aws_tools
            aws_tools = create_aws_tools()
            logger.info(f"✅ Loaded {len(aws_tools)} AWS provider tools")
        except Exception as e:
            logger.warning(f"Failed to load AWS provider tools: {str(e)}")

        # Import and initialize GCP provider tools
        logger.info("Loading GCP provider tools...")
        try:
            from .tools.providers.gcp import create_gcp_tools
            gcp_tools = create_gcp_tools()
            logger.info(f"✅ Loaded {len(gcp_tools)} GCP provider tools")
        except Exception as e:
            logger.warning(f"Failed to load GCP provider tools: {str(e)}")

        # Import and initialize documentation tools
        logger.info("Loading documentation tools...")
        try:
            from .tools.providers.docs import create_doc_tools
            doc_tools = create_doc_tools()
            logger.info(f"✅ Loaded {len(doc_tools)} documentation tools")
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