import sys
import json
import asyncio
import time
from typing import Optional

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

async def manage_network(
    client,
    action: str,
    network_name: str,
    driver: Optional[str] = None,
    subnet: Optional[str] = None
) -> dict:
    try:
        log_status("starting", f"Initializing network {action} operation")

        # Validate inputs
        if not network_name:
            raise ValueError("Network name is required")
        if action not in ["create", "connect", "disconnect", "remove"]:
            raise ValueError(f"Invalid action: {action}")

        if action == "create":
            log_status("progress", "Creating network", network_name=network_name)
            try:
                network = client.network(network_name)
                if driver:
                    network = network.with_driver(driver)
                if subnet:
                    network = network.with_subnet(subnet)
                network_id = await network.id()
                
                result = {
                    "status": "success",
                    "message": "Network created successfully",
                    "network_id": network_id,
                    "network_name": network_name,
                    "driver": driver,
                    "subnet": subnet
                }
                log_status("success", "Network created successfully", **result)
                return result

            except Exception as e:
                raise RuntimeError(f"Failed to create network: {str(e)}")

        elif action == "connect":
            log_status("progress", "Connecting to network", network_name=network_name)
            try:
                # Network connection logic here
                result = {
                    "status": "success",
                    "message": f"Connected to network {network_name}",
                    "network_name": network_name
                }
                log_status("success", "Network connection successful", **result)
                return result

            except Exception as e:
                raise RuntimeError(f"Failed to connect to network: {str(e)}")

        elif action == "disconnect":
            log_status("progress", "Disconnecting from network", network_name=network_name)
            try:
                # Network disconnection logic here
                result = {
                    "status": "success",
                    "message": f"Disconnected from network {network_name}",
                    "network_name": network_name
                }
                log_status("success", "Network disconnection successful", **result)
                return result

            except Exception as e:
                raise RuntimeError(f"Failed to disconnect from network: {str(e)}")

        elif action == "remove":
            log_status("progress", "Removing network", network_name=network_name)
            try:
                # Network removal logic here
                result = {
                    "status": "success",
                    "message": f"Removed network {network_name}",
                    "network_name": network_name
                }
                log_status("success", "Network removal successful", **result)
                return result

            except Exception as e:
                raise RuntimeError(f"Failed to remove network: {str(e)}")

    except Exception as e:
        error_details = {
            "error_type": type(e).__name__,
            "details": str(e),
            "network_name": network_name
        }
        log_status("error", str(e), **error_details)
        return {"status": "error", **error_details}

async def main():
    try:
        # Try to import dagger
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

        required_fields = ["action", "network_name"]
        missing_fields = [field for field in required_fields if field not in args]
        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

        try:
            async with dagger.Connection() as client:
                await manage_network(
                    client,
                    args["action"],
                    args["network_name"],
                    args.get("driver"),
                    args.get("subnet")
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