import os
import json
import logging
import distutils.errors
from typing import Any, Dict

import sentry_sdk
from fastapi import APIRouter, HTTPException, status
from sentry_sdk.integrations.fastapi import FastApiIntegration

from ..core import run_tool, load_workflows_and_tools, run_workflow_with_progress
from ..serialization import KubiyaJSONEncoder
from .models.requests import (
    RunRequest,
    DescribeRequest,
    DiscoverRequest,
    VisualizeRequest,
)

# Set up logging
logger = logging.getLogger("kubiya_sdk")
logging.basicConfig(level=logging.INFO)

# Set up Sentry if DSN is provided
sentry_dsn = os.environ.get("SENTRY_DSN")
if sentry_dsn:
    sentry_sdk.init(dsn=sentry_dsn, integrations=[FastApiIntegration()], traces_sample_rate=1.0)
    logger.info("Sentry monitoring initialized")
else:
    logger.warning("SENTRY_DSN not found in environment variables. Sentry monitoring is disabled.")

router = APIRouter()


@router.post(
    "/discover",
    response_model=Dict[str, Any],
    responses={
        400: {"description": "Bad Request"},
        404: {"description": "Not Found"},
        422: {"description": "Unprocessable Entity"},
        500: {"description": "Internal Server Error"},
    },
)
async def discover_endpoint(request: DiscoverRequest):
    if not request.source:
        logger.error("Invalid request: source is required")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Source is required")

    try:
        logger.info(f"Discovering workflows and tools from source: {request.source}")
        results = load_workflows_and_tools(request.source)

        if not results:
            logger.warning(f"No workflows or tools found in source: {request.source}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No workflows or tools found",
            )

        return json.loads(json.dumps(results, cls=KubiyaJSONEncoder))
    except distutils.errors.DistutilsArgError as e:
        logger.warning(f"Invalid setup command in the source '{request.source}': {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid setup command: {str(e)}",
        )
    except SystemExit as e:
        logger.warning(f"System exit encountered while processing '{request.source}': {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"System exit encountered: {str(e)}",
        )
    except json.JSONDecodeError as e:
        logger.error(f"JSON encoding error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error encoding response: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Unexpected error during discovery: {str(e)}", exc_info=True)
        if sentry_dsn:
            sentry_sdk.capture_exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}",
        )


@router.post(
    "/run",
    responses={
        400: {"description": "Bad Request"},
        404: {"description": "Not Found"},
        422: {"description": "Unprocessable Entity"},
        500: {"description": "Internal Server Error"},
    },
)
async def run_endpoint(request: RunRequest):
    try:
        logger.info(f"Running workflow or tool '{request.name}' from source: {request.source}")
        results = load_workflows_and_tools(request.source)
        workflow = next((w for w in results["workflows"] if w["name"] == request.name), None)
        tool = next((t for t in results["tools"] if t.name == request.name), None)

        if workflow:
            logger.debug(f"Running workflow: {request.name}")
            result = run_workflow_with_progress(workflow["instance"], request.inputs)
            return list(result)
        elif tool:
            logger.debug(f"Running tool: {request.name}")
            result = await run_tool(tool, request.inputs)
            return result
        else:
            logger.warning(f"Workflow or tool '{request.name}' not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow or tool '{request.name}' not found",
            )
    except distutils.errors.DistutilsArgError as e:
        logger.warning(f"Invalid setup command in the source '{request.source}': {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid setup command: {str(e)}",
        )
    except SystemExit as e:
        logger.warning(f"System exit encountered while processing '{request.source}': {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"System exit encountered: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Unexpected error during run: {str(e)}", exc_info=True)
        if sentry_dsn:
            sentry_sdk.capture_exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}",
        )


@router.post(
    "/describe",
    responses={
        400: {"description": "Bad Request"},
        404: {"description": "Not Found"},
        422: {"description": "Unprocessable Entity"},
        500: {"description": "Internal Server Error"},
    },
)
async def describe_endpoint(request: DescribeRequest):
    try:
        logger.info(f"Describing workflow or tool '{request.name}' from source: {request.source}")
        results = load_workflows_and_tools(request.source)
        workflow = next((w for w in results["workflows"] if w["name"] == request.name), None)
        tool = next((t for t in results["tools"] if t.name == request.name), None)

        if workflow:
            logger.debug(f"Describing workflow: {request.name}")
            description = {
                "type": "workflow",
                "name": workflow["name"],
                "description": workflow["instance"].description,
                "steps": [
                    {
                        "name": name,
                        "description": step.description,
                        "icon": step.icon,
                        "label": step.label,
                        "next_steps": step.next_steps,
                        "conditions": step.conditions,
                    }
                    for name, step in workflow["instance"].steps.items()
                ],
                "entry_point": workflow["instance"].entry_point,
            }
        elif tool:
            logger.debug(f"Describing tool: {request.name}")
            description = {
                "type": "tool",
                "name": tool.name,
                "description": tool.description,
                "args": [arg.dict() for arg in tool.args],
                "env": tool.env,
            }
        else:
            logger.warning(f"Workflow or tool '{request.name}' not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow or tool '{request.name}' not found",
            )

        return json.loads(json.dumps(description, cls=KubiyaJSONEncoder))
    except distutils.errors.DistutilsArgError as e:
        logger.warning(f"Invalid setup command in the source '{request.source}': {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid setup command: {str(e)}",
        )
    except SystemExit as e:
        logger.warning(f"System exit encountered while processing '{request.source}': {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"System exit encountered: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Unexpected error during describe: {str(e)}", exc_info=True)
        if sentry_dsn:
            sentry_sdk.capture_exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}",
        )


@router.post(
    "/visualize",
    responses={
        400: {"description": "Bad Request"},
        404: {"description": "Not Found"},
        422: {"description": "Unprocessable Entity"},
        500: {"description": "Internal Server Error"},
    },
)
async def visualize_endpoint(request: VisualizeRequest):
    try:
        logger.info(f"Visualizing workflow '{request.workflow}' from source: {request.source}")
        results = load_workflows_and_tools(request.source)
        workflow = next((w for w in results["workflows"] if w["name"] == request.workflow), None)

        if workflow:
            logger.debug(f"Generating Mermaid diagram for workflow: {request.workflow}")
            mermaid_diagram = workflow["instance"].to_mermaid()
            return {"name": request.workflow, "diagram": mermaid_diagram}
        else:
            logger.warning(f"Workflow '{request.workflow}' not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow '{request.workflow}' not found",
            )
    except distutils.errors.DistutilsArgError as e:
        logger.warning(f"Invalid setup command in the source '{request.source}': {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid setup command: {str(e)}",
        )
    except SystemExit as e:
        logger.warning(f"System exit encountered while processing '{request.source}': {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"System exit encountered: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Unexpected error during visualization: {str(e)}", exc_info=True)
        if sentry_dsn:
            sentry_sdk.capture_exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}",
        )
