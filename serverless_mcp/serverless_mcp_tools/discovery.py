import os
import json
import subprocess
import tempfile
import shutil
import importlib.util
import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MCPToolParameterSchema(BaseModel):
    name: str
    type: str  # Simplified type (e.g., 'string', 'integer', 'boolean', 'number', 'object', 'array')
    description: Optional[str] = None
    required: bool = True
    default: Optional[Any] = None
    # Add more fields if needed based on full MCP schema (e.g., enum, constraints)

class DiscoveredMCPToolSchema(BaseModel):
    name: str
    description: Optional[str] = None
    parameters: List[MCPToolParameterSchema] = Field(default_factory=list)
    # Potentially add: tags, annotations, etc. if needed

class DiscoveredServerInfo(BaseModel):
    config: Dict[str, Any] # The original config entry from servers_to_sync.json
    tools: List[DiscoveredMCPToolSchema]

def _get_parameter_type(annotation: Any) -> str:
    """Converts Python type annotation to a simplified string type."""
    # This is a very basic conversion, needs enhancement for complex types,
    # Optional, Union, Literal, Pydantic models, etc.
    # Should align with Kubiya Arg types eventually.
    type_mapping = {
        str: 'string',
        int: 'integer',
        float: 'number',
        bool: 'boolean',
        dict: 'object',
        list: 'array',
        bytes: 'string', # Represent binary as base64 string?
        # Add more complex mappings
    }
    origin = getattr(annotation, '__origin__', None)
    if origin is list or origin is List:
        return 'array'
    if origin is dict or origin is Dict:
        return 'object'
    # Add handling for Union, Optional, Literal, Pydantic models etc.
    return type_mapping.get(annotation, 'string') # Default to string if unknown


def _discover_tools_in_file(file_path: str, mcp_instance_name: str) -> List[DiscoveredMCPToolSchema]:
    """
    Inspects a Python file to find FastMCP tool definitions.
    This uses dynamic import, which is generally risky but necessary here.
    It assumes the file can be imported without side effects beyond defining the MCP instance.
    It also assumes 'fastmcp' is installed in the environment running this discovery.
    """
    discovered_tools = []
    try:
        from fastmcp import FastMCP # Ensure fastmcp is available

        spec = importlib.util.spec_from_file_location("mcp_module", file_path)
        if not spec or not spec.loader:
            logger.error(f"Could not create module spec for {file_path}")
            return []

        mcp_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mcp_module)

        mcp_instance = getattr(mcp_module, mcp_instance_name, None)
        if not mcp_instance or not isinstance(mcp_instance, FastMCP):
            logger.error(f"MCP instance '{mcp_instance_name}' not found or not a FastMCP instance in {file_path}")
            return []

        # Access the registered tools via the internal dictionary (may change in future fastmcp versions)
        # Ideally, fastmcp would offer a public API for schema introspection.
        registered_tools = getattr(mcp_instance, '_tools', {})

        for tool_name, tool_object in registered_tools.items():
            # tool_object is often a wrapper; need to get the original function
            # and its schema. FastMCP stores schema info internally.
            # This part is highly dependent on fastmcp internal structure and needs refinement.
            # Let's assume `tool_object` has schema info accessible.
            # Placeholder: Extracting schema details would require deeper introspection
            # or a better API from fastmcp. For now, we'll simulate basic discovery.

            # Simulating schema extraction:
            func = getattr(tool_object, '__wrapped__', tool_object) # Try to get original func
            docstring = getattr(func, '__doc__', None)
            sig = inspect.signature(func)

            params_schema = []
            for name, param in sig.parameters.items():
                if name == 'ctx' and param.annotation.__name__ == 'Context': # Skip MCP Context
                    continue

                params_schema.append(MCPToolParameterSchema(
                    name=name,
                    type=_get_parameter_type(param.annotation),
                    description=None, # TODO: Extract from Field description if available
                    required=(param.default is inspect.Parameter.empty),
                    default=None if param.default is inspect.Parameter.empty else param.default
                ))


            discovered_tools.append(DiscoveredMCPToolSchema(
                name=tool_name,
                description=docstring, # Or tool_object.description if set explicitly
                parameters=params_schema
            ))

        logger.info(f"Discovered {len(discovered_tools)} tools in {file_path}")
        return discovered_tools

    except ImportError as e:
        logger.error(f"Failed to import fastmcp or a dependency for {file_path}: {e}. Ensure fastmcp is installed.")
        return []
    except Exception as e:
        logger.error(f"Failed to discover tools in {file_path}: {e}")
        return []

def discover_mcp_tools_from_config(config_path: str) -> List[DiscoveredServerInfo]:
    """
    Reads the configuration file, clones repositories, and discovers MCP tools.
    Requires 'git' command to be available.
    """
    if not os.path.exists(config_path):
        logger.error(f"Configuration file not found: {config_path}")
        return []

    try:
        with open(config_path, 'r') as f:
            server_configs = json.load(f)
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in configuration file: {config_path}")
        return []

    discovered_servers: List[DiscoveredServerInfo] = []
    temp_dir = tempfile.mkdtemp(prefix="kubiya_mcp_discovery_")
    logger.info(f"Using temporary directory for cloning: {temp_dir}")

    # Requires 'inspect' module for signature analysis
    global inspect
    import inspect

    try:
        for config in server_configs:
            repo_url = config.get("git_repo_url")
            branch = config.get("git_branch_or_tag", "main")
            server_file_rel_path = config.get("server_file_path")
            mcp_instance_name = config.get("mcp_instance_name", "mcp")

            if not all([repo_url, server_file_rel_path]):
                logger.warning(f"Skipping invalid config entry: {config}")
                continue

            repo_local_path = os.path.join(temp_dir, config.get("id", os.path.basename(repo_url).replace('.git', '')))
            logger.info(f"Cloning {repo_url} (branch: {branch}) into {repo_local_path}")

            try:
                # Use subprocess to run git clone
                subprocess.run(
                    ["git", "clone", "--depth", "1", "--branch", branch, repo_url, repo_local_path],
                    check=True, capture_output=True, text=True
                )
            except FileNotFoundError:
                logger.error("Git command not found. Please ensure git is installed and in the PATH.")
                # Skip remaining clones if git isn't found
                raise
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to clone repository {repo_url}: {e.stderr}")
                continue # Skip this repo

            server_file_full_path = os.path.join(repo_local_path, server_file_rel_path)
            if not os.path.exists(server_file_full_path):
                logger.error(f"Server file '{server_file_rel_path}' not found in cloned repo {repo_local_path}")
                continue

            # Add repo path to sys.path temporarily for imports within the server file
            import sys
            original_sys_path = list(sys.path)
            sys.path.insert(0, repo_local_path)

            discovered_tools = _discover_tools_in_file(server_file_full_path, mcp_instance_name)

            # Restore sys.path
            sys.path = original_sys_path

            if discovered_tools:
                discovered_servers.append(DiscoveredServerInfo(
                    config=config,
                    tools=discovered_tools
                ))

    except FileNotFoundError:
         # Handled specific git error above, re-raise or log general missing file
         logger.error("A required command (like git) was not found.")
    except Exception as e:
        logger.exception(f"An unexpected error occurred during MCP discovery: {e}")
    finally:
        logger.info(f"Cleaning up temporary directory: {temp_dir}")
        shutil.rmtree(temp_dir, ignore_errors=True)

    logger.info(f"Discovery complete. Found tools from {len(discovered_servers)} servers.")
    return discovered_servers

# Example usage (for testing)
if __name__ == '__main__':
    # Assumes a config file exists at ../config/servers_to_sync.json relative to this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_file = os.path.join(script_dir, '..', 'config', 'servers_to_sync.json')
    print(f"Looking for config at: {config_file}")
    results = discover_mcp_tools_from_config(config_file)
    print(json.dumps([server.dict() for server in results], indent=2))

    # You would need a dummy git repo with a dummy fastmcp server file
    # and fastmcp installed in your environment to test this properly. 