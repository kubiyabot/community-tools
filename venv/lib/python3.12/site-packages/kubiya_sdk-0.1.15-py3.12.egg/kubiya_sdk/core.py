from typing import Any, Dict, List, Union, AsyncGenerator

import jmespath
from pydantic import BaseModel, ValidationError

from kubiya_sdk.tools.models import Tool
from kubiya_sdk.utils.discovery import discover_workflows_and_tools
from kubiya_sdk.workflows.stateful_workflow import StatefulWorkflow


def load_workflows_and_tools(source: str) -> Dict[str, List[Dict[str, Any]]]:
    return discover_workflows_and_tools(source)


async def run_workflow_with_progress(
    workflow: StatefulWorkflow, inputs: Dict[str, Any]
) -> AsyncGenerator[Dict[str, Any], None]:
    async for step_result in workflow.run(inputs):
        yield step_result


async def run_tool(tool: Tool, inputs: Dict[str, Any]) -> Dict[str, Any]:
    return await tool.execute(inputs)


def apply_filter(data: Dict[str, Any], filter_query: str) -> Any:
    return jmespath.search(filter_query, data)


def validate_inputs(schema_or_args: Union[BaseModel, List[Dict[str, Any]]], inputs: Dict[str, Any]) -> Dict[str, Any]:
    if isinstance(schema_or_args, type) and issubclass(schema_or_args, BaseModel):
        try:
            validated = schema_or_args(**inputs)
            return validated.dict()
        except ValidationError as e:
            raise ValueError(f"Invalid inputs: {str(e)}")
    elif isinstance(schema_or_args, list):
        validated_inputs = {}
        for arg in schema_or_args:
            if arg["name"] in inputs:
                if arg["type"]:
                    try:
                        validated_inputs[arg["name"]] = eval(arg["type"])(inputs[arg["name"]])
                    except ValueError:
                        raise ValueError(f"Invalid type for argument '{arg['name']}'. Expected {arg['type']}")
                else:
                    validated_inputs[arg["name"]] = inputs[arg["name"]]
            elif arg.get("required", True):
                raise ValueError(f"Required argument '{arg['name']}' is missing")
            elif "default" in arg:
                validated_inputs[arg["name"]] = arg["default"]
        return validated_inputs
    else:
        raise ValueError("Invalid schema or args provided for input validation")
