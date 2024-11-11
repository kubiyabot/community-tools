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