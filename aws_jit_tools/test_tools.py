import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

def main():
    print("Starting tool generation test...")
    
    # Import and initialize tools
    import aws_jit_tools
    
    # Tools are automatically initialized when the module is imported
    print("\nRegistered tools:")
    from kubiya_sdk.tools.registry import tool_registry
    tools = tool_registry.get_tools("aws_jit")
    for tool in tools:
        print(f"- {tool.name}: {tool.description}")

if __name__ == "__main__":
    main() 