import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

from aws_jit_tools.tools.generator import ToolGenerator

def main():
    print("Starting tool generation test...")
    
    # Create generator
    generator = ToolGenerator()
    
    # Generate tools
    tools = generator.generate_tools()
    
    print(f"\nGenerated {len(tools)} tools:")
    for tool in tools:
        print(f"- {tool.name}: {tool.description}")

if __name__ == "__main__":
    main() 