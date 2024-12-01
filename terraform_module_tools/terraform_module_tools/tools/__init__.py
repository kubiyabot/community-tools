from .module_tools import initialize_module_tools

# Initialize tools when the module is imported
initialize_module_tools()

__all__ = ['initialize_module_tools', 'TerraformModuleTool']