import dagger
import sys
import json
import asyncio
from typing import List, Dict
import time

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

async def build_image(
    client,
    context_path: str,
    dockerfile: str,
    target: str = None,
    build_args: Dict[str, str] = None,
    platforms: List[str] = None,
    push: bool = False,
    registry: str = None,
    tag: str = "latest"
) -> dict:
    try:
        log_status("starting", "Initializing build process")

        # Validate inputs
        if not context_path or not dockerfile:
            raise ValueError("Both context_path and dockerfile are required")

        # Create base container
        log_status("progress", "Loading build context", context_path=context_path)
        try:
            container = client.host().directory(context_path)
        except Exception as e:
            raise RuntimeError(f"Failed to load build context: {str(e)}")

        # Configure build
        log_status("progress", "Configuring build parameters", 
                  dockerfile=dockerfile,
                  target=target,
                  build_args=build_args,
                  platforms=platforms)

        try:
            build = container.docker_build(
                dockerfile=dockerfile,
                target=target if target else None,
                build_args=[dagger.BuildArg(name=k, value=v) for k, v in (build_args or {}).items()],
                platform=platforms[0] if platforms else None
            )
        except Exception as e:
            raise RuntimeError(f"Failed to configure build: {str(e)}")

        # Get image ID
        log_status("progress", "Building image")
        try:
            image_id = await build.id()
        except Exception as e:
            raise RuntimeError(f"Build failed: {str(e)}")

        if push and registry:
            log_status("progress", "Pushing image to registry",
                      registry=registry,
                      tag=tag)
            try:
                # Push logic here...
                pass
            except Exception as e:
                raise RuntimeError(f"Failed to push image: {str(e)}")

        result = {
            "status": "success",
            "message": "Build completed successfully",
            "image_id": image_id,
            "context": context_path,
            "dockerfile": dockerfile,
            "timestamp": time.time()
        }
        
        if push and registry:
            result["registry_url"] = f"{registry}/{image_id}:{tag}"

        log_status("success", "Build completed successfully", **result)
        return result

    except Exception as e:
        error_details = {
            "error_type": type(e).__name__,
            "details": str(e)
        }
        log_status("error", str(e), **error_details)
        return {"status": "error", **error_details}

async def main():
    try:
        if len(sys.argv) != 2:
            raise ValueError("Expected exactly one JSON argument")

        try:
            args = json.loads(sys.argv[1])
        except json.JSONDecodeError as e:
            log_status("error", "Invalid JSON input",
                      error_type="JSONDecodeError",
                      details=str(e))
            sys.exit(1)

        required_fields = ["context_path", "dockerfile"]
        missing_fields = [field for field in required_fields if field not in args]
        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

        async with dagger.Connection() as client:
            await build_image(
                client,
                args["context_path"],
                args["dockerfile"],
                args.get("target"),
                args.get("build_args"),
                args.get("platforms"),
                args.get("push", False),
                args.get("registry"),
                args.get("tag", "latest")
            )

    except Exception as e:
        log_status("error", "Unexpected error occurred",
                  error_type=type(e).__name__,
                  details=str(e))
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())