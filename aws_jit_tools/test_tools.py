import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

logger = logging.getLogger(__name__)

def main():
    logger.info("Starting tool generation test...")
    
    # Import and initialize tools
    import aws_jit_tools
    
    # Check registered tools
    from kubiya_sdk.tools.registry import tool_registry
    
    # Get all registered tools
    all_tools = tool_registry.get_tools("aws_jit")
    logger.info(f"Found {len(all_tools)} registered tools:")
    
    for tool in all_tools:
        logger.info(f"- {tool.name}: {tool.description}")
        logger.info(f"  Type: {tool.type}")
        logger.info(f"  Environment vars: {tool.env}")
        logger.info("  " + "-" * 40)

if __name__ == "__main__":
    main() 