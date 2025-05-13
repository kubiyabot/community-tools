import os
import logging
from typing import List
from kubiya_sdk.tools import Tool, Arg


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define the name for the Docker image that will be built for the discovery tool
# This image name should be used when building Dockerfile.discover_tool
DISCOVER_TOOL_IMAGE_NAME = "your-docker-registry/mcp-discovery-tool:latest"

def get_tools() -> List[Tool]:
    """
    Main function called by Kubiya to load tools.
    It defines and returns the single 'DiscoverAndDefineMCPTools' meta-tool.
    """
    logger.info("Defining the 'DiscoverAndDefineMCPTools' meta-tool...")

    # Arguments for the DiscoverAndDefineMCPTools tool itself, if any.
    # For now, it reads its config from a file inside its Docker image.
    # If KUBIYA_API_KEY were strictly needed by the script, it could be an Arg
    # or more securely, a Secret.
    discover_tool_args = [
        # Example if we wanted to pass the config path or API key as an arg:
        # Arg(
        #     name="config_json_base64", 
        #     type=KubiyaArgType.STRING, 
        #     description="Base64 encoded JSON string of the servers_to_sync.json content.",
        #     required=False 
        # ),
        # Arg(
        #     name="kubiya_api_key_env_name",
        #     type=KubiyaArgType.STRING,
        #     description="Name of the environment variable holding the Kubiya API Key for potential direct registration (optional).",
        #     required=False,
        #     default_value="KUBIYA_API_KEY"
        # )
    ]

    # The discover_exec_script.py is now the main program for this tool's container.
    # The Dockerfile.discover_tool copies it to /kubiya_tool_app/discover_exec_script.py and sets it as ENTRYPOINT.
    # So, `content` for a Docker tool type usually refers to a command override for the entrypoint, 
    # or can be empty if the Docker image's ENTRYPOINT is sufficient.
    # Since our Dockerfile.discover_tool has a fixed ENTRYPOINT, content can be minimal or used for args if not passed via env.

    discover_and_define_tool = Tool(
        name="DiscoverAndDefineMCPTools",
        description="Discovers FastMCP tools from configured repositories and outputs their Kubiya tool definitions as JSON. The output of this tool is intended to be used by a tool manager to register the defined tools in Kubiya.",
        type="docker",
        image=DISCOVER_TOOL_IMAGE_NAME, # You need to build and push this image
        # The content for a Docker tool is the command to run. 
        # Since Dockerfile.discover_tool has an ENTRYPOINT, content might not be strictly needed 
        # unless overriding or passing specific shell commands. 
        # If discover_exec_script.py is the ENTRYPOINT, content can be empty.
        content="", # Let the Docker image's ENTRYPOINT handle execution.
        args=discover_tool_args,
        icon_url="https://raw.githubusercontent.com/kubiyabot/kubiya-community-tools/main/catalog/logos/kubiya_sdk.png", # Generic SDK icon
        # This meta-tool itself does not run other services directly.
        # The definitions it *outputs* will contain service specs for the actual MCP tools.
        with_services=[], 
        # If the discover_exec_script.py needs KUBIYA_API_KEY, it should be passed as a secret.
        secrets=[], # Example: [Secret(name="kubiya-api-key", mount_path="/etc/secrets/kubiya_api_key")]
        env={}
    )

    logger.info(f"'DiscoverAndDefineMCPTools' meta-tool defined with image: {DISCOVER_TOOL_IMAGE_NAME}")
    return [discover_and_define_tool]

# For direct testing of this loader itself (python -m serverless_mcp.loader)
if __name__ == '__main__':
    tools = get_tools()
    if tools:
        print("--- Defined Meta-Tool ---")
        print(f"Tool Name: {tools[0].name}")
        print(f"  Description: {tools[0].description}")
        print(f"  Image: {tools[0].image}")
        print("-----")
    else:
        print("No meta-tool was defined.") 