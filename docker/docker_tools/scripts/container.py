import sys
import json
import asyncio
import time
from typing import Optional, Dict, List, Any

def log_status(status: str, message: str, **kwargs):
    """Helper function to format and print status messages"""
    output = {
        "status": status,
        "message": message,
        "timestamp": time.time(),
        **kwargs
    }
    if status == "error":
        print(json.dumps(output), file=sys.stderr)
    else:
        print(json.dumps(output))

async def manage_container(
    client: Any,
    action: str,
    container_id: Optional[str] = None,
    image: Optional[str] = None,
    command: Optional[List[str]] = None,
    env: Optional[Dict[str, str]] = None,
    ports: Optional[List[int]] = None
) -> dict:
    try:
        log_status("starting", f"Initializing container {action} operation")

        # Validate inputs
        if action not in ["run", "stop", "logs"]:
            raise ValueError(f"Invalid action: {action}")

        if action == "run":
            if not image:
                raise ValueError("Image is required for 'run' action")

            log_status("progress", "Creating container", image=image)
            try:
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
                result = {
                    "status": "success",
                    "container_id": container_id,
                    "image": image
                }
                log_status("success", "Container created successfully", **result)
                return result
                
            except Exception as e:
                raise RuntimeError(f"Failed to create container: {str(e)}")
            
        elif action == "stop":
            if not container_id:
                raise ValueError("Container ID is required for 'stop' action")

            log_status("progress", "Stopping container", container_id=container_id)
            try:
                container = client.container(id=container_id)
                await container.stop()
                result = {
                    "status": "success",
                    "message": f"Container {container_id} stopped",
                    "container_id": container_id
                }
                log_status("success", "Container stopped successfully", **result)
                return result
                
            except Exception as e:
                raise RuntimeError(f"Failed to stop container: {str(e)}")
            
        elif action == "logs":
            if not container_id:
                raise ValueError("Container ID is required for 'logs' action")

            log_status("progress", "Fetching container logs", container_id=container_id)
            try:
                container = client.container(id=container_id)
                logs = await container.logs()
                result = {
                    "status": "success",
                    "logs": logs,
                    "container_id": container_id
                }
                log_status("success", "Container logs retrieved successfully", **result)
                return result
                
            except Exception as e:
                raise RuntimeError(f"Failed to get container logs: {str(e)}")
            
    except Exception as e:
        error_details = {
            "error_type": type(e).__name__,
            "details": str(e),
            "action": action,
            "container_id": container_id,
            "image": image
        }
        log_status("error", str(e), **error_details)
        return {"status": "error", **error_details}

async def main():
    try:
        # Try to import required packages
        try:
            import dagger
        except ImportError as e:
            log_status("error", "Failed to import dagger SDK. Please ensure it's installed.",
                      error_type="ImportError",
                      details=str(e))
            sys.exit(1)

        if len(sys.argv) != 2:
            raise ValueError("Expected exactly one JSON argument")

        try:
            args = json.loads(sys.argv[1])
        except json.JSONDecodeError as e:
            log_status("error", "Invalid JSON input",
                      error_type="JSONDecodeError",
                      details=str(e))
            sys.exit(1)

        required_fields = ["action"]
        missing_fields = [field for field in required_fields if field not in args]
        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

        try:
            async with dagger.Connection() as client:
                await manage_container(
                    client,
                    args["action"],
                    args.get("container_id"),
                    args.get("image"),
                    args.get("command"),
                    args.get("env"),
                    args.get("ports")
                )
        except Exception as e:
            log_status("error", "Failed to connect to Dagger engine",
                      error_type=type(e).__name__,
                      details=str(e))
            sys.exit(1)

    except Exception as e:
        log_status("error", "Unexpected error occurred",
                  error_type=type(e).__name__,
                  details=str(e))
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())