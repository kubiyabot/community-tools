from kubiya_sdk.tools import Tool, Arg, ServiceSpec, KubiyaArgType
from kubiya_sdk.tools.secret import Secret
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

# Placeholder for the MCP service runner image. Replace with your actual image URI.
MCP_SERVICE_IMAGE = "your-docker-registry/mcp-service-runner:latest"
DEFAULT_TOOL_ICON = "https://raw.githubusercontent.com/kubiyabot/kubiya-community-tools/main/catalog/logos/fastmcp.png"

class ServerlessMCPTool(Tool):
    def __init__(self, mcp_server_config: Dict[str, Any], tool_schema: Dict[str, Any]):
        self.mcp_server_config = mcp_server_config
        self.tool_schema = tool_schema

        kubiya_args = self._convert_mcp_params_to_kubiya_args(tool_schema.get('parameters', []))

        # Unique service name for this MCP server
        # Ensure service name is DNS-1123 compliant (lowercase alphanumeric, -, .)
        service_id = mcp_server_config.get("id", "default-mcp-server").lower().replace("_", "-")
        mcp_service_name = f"mcp-svc-{service_id}"
        mcp_service_port = mcp_server_config.get("service_port", 8000)

        # Base environment variables for the MCP service container
        service_env = {
            "GIT_REPO_URL": mcp_server_config["git_repo_url"],
            "GIT_BRANCH_OR_TAG": mcp_server_config["git_branch_or_tag"],
            "SERVER_FILE_PATH": mcp_server_config["server_file_path"],
            "MCP_INSTANCE_NAME": mcp_server_config["mcp_instance_name"],
            "SERVICE_PORT": str(mcp_service_port) # Env vars must be strings
        }

        # Add any custom environment variables from server config
        custom_env = mcp_server_config.get("env", {})
        for key, value in custom_env.items():
            service_env[key] = str(value) if value is not None else ""

        # Process secrets from server config
        service_secrets = []
        secrets_config = mcp_server_config.get("secrets", [])
        for secret_config in secrets_config:
            if isinstance(secret_config, dict) and "name" in secret_config:
                # Full secret definition with mount path, etc.
                service_secrets.append(Secret(**secret_config))
            elif isinstance(secret_config, str):
                # Simple secret name, let Kubiya handle default mounting
                service_secrets.append(Secret(name=secret_config))
            else:
                logger.warning(f"Ignoring invalid secret configuration: {secret_config}")

        mcp_service = ServiceSpec(
            name=mcp_service_name,
            image=MCP_SERVICE_IMAGE,
            exposed_ports=[mcp_service_port],
            env=service_env,
            secrets=service_secrets,
            volumes=mcp_server_config.get("volumes", [])  # Optional volume mounts
        )

        # The content script that runs inside the Kubiya tool's container
        # This script will act as a client to the MCP service
        content_script = self._generate_client_script(
            service_host=mcp_service_name, # Kubiya resolves service names
            service_port=mcp_service_port,
            mcp_tool_name=tool_schema['name'],
            mcp_tool_params=tool_schema.get('parameters', [])
        )

        tool_name = f"{mcp_server_config.get('id', 'mcp')}_{tool_schema['name']}"
        tool_description = tool_schema.get('description', f"Dynamically wrapped MCP tool: {tool_schema['name']}")
        tool_icon = mcp_server_config.get("tool_icon_url", DEFAULT_TOOL_ICON)

        super().__init__(
            name=tool_name,
            description=tool_description,
            type="python", # Run python script
            image="python:3.11-slim", # Image for the Kubiya tool itself (client side)
            content=content_script,
            args=kubiya_args,
            icon_url=tool_icon,
            with_services=[mcp_service],
            # Secrets or env vars for the Kubiya tool itself (client side) if needed
            # For example, if the client needs specific API keys not related to the MCP server
            secrets=[],
            env={ # Env for the client tool container
                "KUBIYA_LOG_LEVEL": "INFO" # Example
            }
        )

    def _convert_mcp_params_to_kubiya_args(self, mcp_params: List[Dict[str, Any]]) -> List[Arg]:
        args = []
        for param in mcp_params:
            # Basic type mapping, can be expanded
            # This needs to be more robust based on discovery.py's _get_parameter_type
            # and KubiyaArgType definitions.
            param_type_str = param.get('type', 'string').lower()
            kubiya_type = KubiyaArgType.STRING # Default
            if param_type_str == 'string':
                kubiya_type = KubiyaArgType.STRING
            elif param_type_str == 'integer':
                kubiya_type = KubiyaArgType.NUMBER # Kubiya uses NUMBER for int/float
            elif param_type_str == 'number':
                kubiya_type = KubiyaArgType.NUMBER
            elif param_type_str == 'boolean':
                kubiya_type = KubiyaArgType.BOOLEAN
            elif param_type_str == 'array':
                kubiya_type = KubiyaArgType.LIST
            elif param_type_str == 'object':
                kubiya_type = KubiyaArgType.JSON_OBJECT
            # Add more mappings as necessary (e.g. for files, date, etc.)

            args.append(Arg(
                name=param['name'],
                description=param.get('description', ''),
                type=kubiya_type,
                required=param.get('required', True),
                default_value=param.get('default')
            ))
        return args

    def _generate_client_script(self, service_host: str, service_port: int, mcp_tool_name: str, mcp_tool_params: List[Dict[str, Any]]) -> str:
        # Prepare argument parsing for the client script
        arg_parsing_lines = []
        mcp_call_args = "{"
        for i, param in enumerate(mcp_tool_params):
            param_name = param['name']
            arg_parsing_lines.append(f"    {param_name} = os.getenv('{param_name.upper()}_ARG')")
            # Handle type conversion from string env var to Python type for the call
            # This needs to be robust based on the actual type from schema
            param_type_str = param.get('type', 'string').lower()
            if param_type_str == 'integer':
                arg_parsing_lines.append(f"    if {param_name} is not None: {param_name} = int({param_name})")
            elif param_type_str == 'number': # float
                arg_parsing_lines.append(f"    if {param_name} is not None: {param_name} = float({param_name})")
            elif param_type_str == 'boolean':
                arg_parsing_lines.append(f"    if {param_name} is not None: {param_name} = {param_name}.lower() in ('true', '1', 't')")
            elif param_type_str in ['array', 'object']:
                 arg_parsing_lines.append(f"    if {param_name} is not None: {param_name} = json.loads({param_name})")

            mcp_call_args += f"'{param_name}': {param_name}"
            if i < len(mcp_tool_params) - 1:
                mcp_call_args += ", "
        mcp_call_args += "}"

        client_script = f"""
import asyncio
import os
import json
import logging
from fastmcp import Client

logging.basicConfig(level=os.getenv('KUBIYA_LOG_LEVEL', 'INFO').upper(), format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    logger.info(f'MCP Client: Connecting to MCP service at http://{service_host}:{service_port}')
    mcp_server_address = f'http://{service_host}:{service_port}/mcp' # Assuming default /mcp path for streamable-http

    # Parse arguments passed as environment variables by Kubiya
{'\n'.join(arg_parsing_lines)}

    mcp_tool_name_to_call = '{mcp_tool_name}'
    mcp_tool_arguments = {mcp_call_args}

    logger.info(f'MCP Client: Calling tool {{mcp_tool_name_to_call}} with arguments: {{mcp_tool_arguments}}')

    client = Client(server_url=mcp_server_address)
    async with client:
        try:
            result = await client.call_tool(mcp_tool_name_to_call, mcp_tool_arguments)
            # The result from fastmcp client.call_tool is usually a list of CallToolResult objects.
            # We need to extract the actual content.
            if result and isinstance(result, list) and hasattr(result[0], 'content'):
                # Assuming TextContent or similar that has a .text attribute or can be json serialized
                output = result[0].content
                if hasattr(output, 'text'):
                    print(output.text) # For simple text output
                elif isinstance(output, (dict, list)):
                    print(json.dumps(output)) # For structured output
                else:
                    print(str(output))
            else:
                logger.warning(f'MCP Client: Received unexpected result format: {{result}}')
                print(str(result))

        except Exception as e:
            logger.error(f'MCP Client: Error calling tool {{mcp_tool_name_to_call}}: {{e}}', exc_info=True)
            # Propagate error to Kubiya by printing to stderr or raising an exception
            # For now, printing error message and exiting with non-zero status
            print(f'Error: {{e}}', file=open(os.devnull, 'w') if os.name == 'posix' else None) # Python hides stderr by default in some K8s contexts
            # A more robust way would be to ensure stderr is captured by Kubiya or write to a defined error file.
            raise

if __name__ == '__main__':
    # Install fastmcp if not present (Kubiya image might not have it by default for the tool itself)
    try:
        import fastmcp
    except ImportError:
        import subprocess
        import sys
        logger.info("fastmcp not found, installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "fastmcp>=2.3.0", "httpx"])
        # Re-import or indicate restart might be needed if this was a real script, 
        # but for Kubiya content, it's fine if main() uses it directly after this.

    asyncio.run(main())
"""
        return client_script

    def to_kubiya_definition_dict(self) -> Dict[str, Any]:
        """Serializes the tool's configuration into a dictionary suitable for JSON output."""
        # Assuming ToolType is an Enum and Arg/ServiceSpec have dict() methods from Kubiya SDK
        try:
            definition = {
                "name": self.name,
                "description": self.description,
                "type": self.type.value if hasattr(self.type, 'value') else str(self.type),
                "image": self.image,
                "content": self.content,
                "args": [arg.dict() for arg in self.args],
                "icon_url": self.icon_url,
                "with_services": [service.dict() for service in self.with_services],
                "secrets": self.secrets,
                "env": self.env
                # Add other serializable fields from the base Tool class if necessary
            }
            return definition
        except Exception as e:
            logger.error(f"Failed to serialize tool definition for {self.name}: {e}", exc_info=True)
            # Return a minimal dict or raise an error, depending on desired handling
            return {"name": self.name, "error": f"Serialization failed: {e}"}

    def run(self):
        # This method is called by Kubiya if the tool type is EXECUTOR.
        # For ToolType.PYTHON, the `content` script is executed directly.
        # We don't need to implement `run` here as we are using ToolType.PYTHON.
        logger.warning("ServerlessMCPTool.run() called, but this tool uses ToolType.PYTHON and executes its content script.")
        pass 