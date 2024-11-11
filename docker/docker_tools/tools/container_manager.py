from kubiya_sdk.tools import Arg
from kubiya_sdk.tools.registry import tool_registry
from docker_tools.base import DockerTool

CONTAINER_SCRIPT = """
import dagger
import sys
import json
import asyncio

async def manage_container(client, action, container_id=None, image=None, command=None, env=None, ports=None):
    try:
        if action == "run":
            container = client.container().from_(image)
            
            # Configure container
            if env:
                for key, value in env.items():
                    container = container.with_env_variable(key, value)
            
            if ports:
                for port in ports:
                    container = container.with_exposed_port(port)
            
            if command:
                container = container.with_exec(command)
            
            # Run container
            container_id = await container.id()
            return {"status": "success", "container_id": container_id}
            
        elif action == "stop":
            # Stop container logic
            container = client.container(id=container_id)
            await container.stop()
            return {"status": "success", "message": f"Container {container_id} stopped"}
            
        elif action == "logs":
            # Get container logs
            container = client.container(id=container_id)
            logs = await container.logs()
            return {"status": "success", "logs": logs}
            
    except Exception as e:
        return {"status": "error", "error": str(e)}

async def main():
    args = json.loads(sys.argv[1])
    async with dagger.Connection() as client:
        result = await manage_container(
            client,
            args["action"],
            args.get("container_id"),
            args.get("image"),
            args.get("command"),
            args.get("env"),
            args.get("ports")
        )
        print(json.dumps(result, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
"""

container_manager_tool = DockerTool(
    name="manage-container",
    description="Manage Docker containers - run, stop, and view logs",
    content="""
#!/bin/bash
set -e

echo "🐳 Initializing container management..."
pip install dagger-io > /dev/null 2>&1

ARGS='{
    "action": "'$action'",
    "container_id": "'$container_id'",
    "image": "'$image'",
    "command": '$command',
    "env": '$env',
    "ports": '$ports'
}'

echo "🚀 Executing container operation: $action"
python /tmp/container.py "$ARGS"
    """,
    args=[
        Arg(
            name="action",
            type="str",
            description="Action to perform (run/stop/logs)",
            required=True
        ),
        Arg(
            name="container_id",
            type="str",
            description="Container ID for stop/logs actions",
            required=False
        ),
        Arg(
            name="image",
            type="str",
            description="Image to run for 'run' action",
            required=False
        ),
        Arg(
            name="command",
            type="str",
            description="JSON array of command to run",
            required=False,
            default="[]"
        ),
        Arg(
            name="env",
            type="str",
            description="JSON object of environment variables",
            required=False,
            default="{}"
        ),
        Arg(
            name="ports",
            type="str",
            description="JSON array of ports to expose",
            required=False,
            default="[]"
        )
    ],
    with_files=[
        FileSpec(
            destination="/tmp/container.py",
            content=CONTAINER_SCRIPT
        )
    ],
    long_running=True,  # Container operations can be long-running
    mermaid="""
    stateDiagram-v2
        [*] --> Pending: Create
        Pending --> Running: Start
        Running --> Stopped: Stop
        Stopped --> Running: Start
        Running --> [*]: Remove
        Stopped --> [*]: Remove
        
        state Running {
            [*] --> Active
            Active --> Paused: Pause
            Paused --> Active: Unpause
        }
    """
)

tool_registry.register("docker", container_manager_tool) 