from typing import Dict, Any, List
from kubiya_sdk.tools.registry import tool_registry
from .dynamic_tool_loader import load_terraform_tools as _load_tools

def load_terraform_tools() -> None:
    """
    Load and register all Terraform tools from configuration files.
    
    Raises:
        Exception: If any critical error occurs during tool loading
    """
    errors = []
    
    try:
        # Get initial tool count
        initial_count = len(tool_registry.get_tools())
        print(f"📊 Current tool count before loading: {initial_count}")
        
        # Load tools
        _load_tools()
        
        # Get final tool count
        final_count = len(tool_registry.get_tools())
        print(f"📊 Tool count after loading: {final_count}")
        print(f"📈 New tools added: {final_count - initial_count}")
        
        # List registered terraform tools
        terraform_tools = [
            tool.name 
            for tool in tool_registry.get_tools() 
            if tool.name.startswith('terraform_')
        ]
        if terraform_tools:
            print("\n🔧 Registered Terraform tools:")
            for tool_name in terraform_tools:
                print(f"  - {tool_name}")
        else:
            print("\n⚠️ No Terraform tools were registered!")
            
    except Exception as e:
        errors.append({
            "type": type(e).__name__,
            "message": str(e),
            "details": getattr(e, "errors", None)
        })
    
    if errors:
        error_msg = "Failed to load terraform tools:\n"
        for error in errors:
            error_msg += f"\n- {error['type']}: {error['message']}"
            if error.get('details'):
                error_msg += f"\n  Details: {error['details']}"
        raise Exception(error_msg)

# Export only what's needed
__all__ = ['load_terraform_tools']