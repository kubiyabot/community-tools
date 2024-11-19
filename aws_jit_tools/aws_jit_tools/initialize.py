from .tools.generator import ToolGenerator

def initialize_tools():
    """Initialize and register all JIT access tools."""
    generator = ToolGenerator()
    return generator.generate_tools() 