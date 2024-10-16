# Docker Tools Module for Kubiya SDK

This module provides a set of tools for interacting with Docker using the Kubiya SDK. These tools are designed to be stateless and easily discoverable by the Kubiya engine, allowing for dynamic execution in various environments.

## Tools Overview

1. **image**: Manages Docker images (pull, push, build, list, remove)
2. **container**: Manages Docker containers (create, start, stop, remove, list)
3. **volume**: Manages Docker volumes (create, remove, list)
4. **network**: Manages Docker networks (create, remove, list)

## Architecture and Execution Flow

1. The Kubiya engine discovers and loads the tools defined in this module.
2. When a tool is invoked, it runs in a Docker container with the Docker CLI installed.
3. The tool executes Docker commands using the host's Docker socket, which is mounted into the tool's container.
4. Results are returned to the Kubiya engine for further processing or display.

## Setup and Usage

1. Add this module to your Kubiya environment.
2. Ensure the host running the Kubiya agent has Docker installed and the Docker socket accessible.
3. Use the tools through the Kubiya interface or API.

## Tool Definitions

### Image Tool

Manages Docker images with the following actions:
- pull: Pull an image from a registry
- push: Push an image to a registry
- build: Build an image from a Dockerfile
- list: List available images
- remove: Remove an image

### Container Tool

Manages Docker containers with the following actions:
- create: Create a new container
- start: Start a container
- stop: Stop a running container
- remove: Remove a container
- list: List containers

### Volume Tool

Manages Docker volumes with the following actions:
- create: Create a new volume
- remove: Remove a volume
- list: List volumes

### Network Tool

Manages Docker networks with the following actions:
- create: Create a new network
- remove: Remove a network
- list: List networks

## Adding New Tools

To add a new tool to this module:

1. Create a new Python file in the `docker_tools/tools/` directory.
2. Define your tool using the Kubiya SDK's Tool model.
3. Import and expose your new tool in the `__init__.py` file.
4. Update the module in the source repository.
5. Refresh the source in the Teammate Environment to discover the new tool.

## Contributing

Contributions to this module are welcome! Please ensure that any new tools or modifications maintain the stateless nature of the tools and adhere to the existing pattern of tool definition.

## License

This project is licensed under the MIT License.
