import asyncio
from typing import Any, Dict, AsyncGenerator


async def run_workflow_with_progress(
    workflow, inputs: Dict[str, Any], interactive: bool = True
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Execute a workflow and yield progress updates.

    :param workflow: The workflow to execute
    :param inputs: Input data for the workflow
    :param interactive: Whether to yield intermediate progress updates
    :yield: Status updates and final result
    """
    try:
        steps = list(workflow.steps.keys())
        for step in steps:
            # Simulate workflow step execution
            await asyncio.sleep(1)  # Simulate work
            if interactive:
                yield {"step": step, "status": "completed"}

        # Simulate final workflow result
        result = {
            "result": "Workflow completed",
            "output": f"Processed inputs: {inputs}",
        }
        yield result
    except Exception as e:
        yield {"error": str(e)}


async def run_tool(tool, inputs: Dict[str, Any], interactive: bool = True) -> Dict[str, Any]:
    """
    Execute a tool and return the result.

    :param tool: The tool to execute
    :param inputs: Input data for the tool
    :param interactive: Whether to print status updates
    :return: Tool execution result
    """
    try:
        if interactive:
            print({"status": "running"})

        # Simulate tool execution
        await asyncio.sleep(1)  # Simulate work

        # Simulate tool result
        result = {"result": "Tool executed", "output": f"Processed inputs: {inputs}"}
        return result
    except Exception as e:
        return {"error": str(e)}
