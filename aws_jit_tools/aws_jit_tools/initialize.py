import logging

logger = logging.getLogger(__name__)

def initialize_tools():
    """Initialize and register all JIT access tools."""
    try:
        from .tools.generator import ToolGenerator
        
        logger.info("Creating tool generator...")
        generator = ToolGenerator()
        
        logger.info("Generating tools...")
        tools = generator.generate_tools()
        
        logger.info(f"Successfully generated {len(tools)} tools")
        return tools
    except Exception as e:
        raise e
