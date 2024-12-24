__all__ = [
    'TerraformerTool',
    '_initialize_provider_tools',
    'load_tools',
    'register_tools'
]

# Import and register tools after defining __all__
from .terraformer_tool import TerraformerTool, _initialize_provider_tools
from .dynamic_tool_loader import load_tools, register_tools

# Register tools on import
register_tools()