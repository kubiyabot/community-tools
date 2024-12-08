import logging
import os
from typing import List
from kubiya_sdk.tools.registry import tool_registry
from ..parser import JenkinsJobParser
from .jenkins_job_tool import JenkinsJobTool
from ..scripts.config_loader import get_jenkins_config

logger = logging.getLogger(__name__)

class ToolInitializationError(Exception):
    """Exception raised for errors during tool initialization."""
    pass

def create_jenkins_job_tool(job_config: dict, long_running: bool = False) -> JenkinsJobTool:
    """Create a Jenkins job tool from configuration."""
    try:
        # Generate tool name with self_service prefix
        base_name = job_config['name'].lower().replace(' ', '_')
        tool_name = f"self_service_jenkins_{base_name}"
        
        # Create tool description
        description = (
            f"Execute Jenkins job: {job_config['name']}\n"
            f"{job_config.get('description', '')}\n"
            f"URL: {job_config['url']}"
        )

        logger.debug(f"Creating tool: {tool_name}")
        return JenkinsJobTool(
            name=tool_name,
            description=description,
            job_config=job_config,
            long_running=long_running,
            type="docker",
            image="python:3.9-alpine"
        )
    except Exception as e:
        raise ToolInitializationError(f"Failed to create tool for job {job_config.get('name', 'unknown')}: {str(e)}")

def initialize_tools() -> List[JenkinsJobTool]:
    """Initialize all Jenkins job tools."""
    tools = []
    
    try:
        # Load Jenkins configuration
        config = get_jenkins_config()
        if not config:
            raise ToolInitializationError("Failed to load Jenkins configuration")

        # Get Jenkins credentials
        jenkins_token = os.environ.get(config['auth']['password_env'])
        if not jenkins_token:
            raise ToolInitializationError(f"Environment variable {config['auth']['password_env']} not set")

        logger.info(f"Connecting to Jenkins at {config['jenkins_url']}")
        
        # Initialize parser
        parser = JenkinsJobParser(
            jenkins_url=config['jenkins_url'],
            username=config['auth']['username'],
            api_token=jenkins_token
        )

        # Get job filter based on configuration
        job_filter = None
        if not config.get('jobs', {}).get('sync_all', False):
            include_jobs = set(config.get('jobs', {}).get('include', []))
            exclude_jobs = set(config.get('jobs', {}).get('exclude', []))
            if include_jobs:
                job_filter = list(include_jobs - exclude_jobs)
                logger.info(f"Using job filter: {job_filter}")

        # Get jobs from Jenkins
        logger.info("Fetching jobs from Jenkins...")
        jobs_info, warnings, errors = parser.get_jobs(job_filter)

        # Log any warnings or errors
        for warning in warnings:
            logger.warning(warning)
        for error in errors:
            logger.error(error)

        if errors:
            raise ToolInitializationError(f"Errors occurred during job discovery: {'; '.join(errors)}")

        if not jobs_info:
            raise ToolInitializationError("No jobs were discovered from Jenkins")

        # Create tools for each job
        for job_name, job_info in jobs_info.items():
            try:
                # Skip non-buildable jobs
                if not job_info.get('buildable', True):
                    logger.warning(f"Skipping non-buildable job: {job_name}")
                    continue

                # Create regular tool
                tool = create_jenkins_job_tool(job_info)
                tools.append(tool)
                tool_registry.register("jenkins", tool)
                logger.info(f"Created tool for job: {job_name}")

                # Create long-running version if needed
                if job_info.get('long_running', False):
                    long_running_tool = create_jenkins_job_tool(job_info, long_running=True)
                    long_running_tool.name += "_long_running"
                    tools.append(long_running_tool)
                    tool_registry.register("jenkins", long_running_tool)
                    logger.info(f"Created long-running tool for job: {job_name}")

            except Exception as e:
                raise ToolInitializationError(f"Failed to create tool for job {job_name}: {str(e)}")

        if not tools:
            raise ToolInitializationError("No tools were created from discovered jobs")

        logger.info(f"Successfully created {len(tools)} tools")
        return tools

    except Exception as e:
        error_msg = f"Failed to initialize tools: {str(e)}"
        logger.error(error_msg)
        raise ToolInitializationError(error_msg) from e

__all__ = ['initialize_tools', 'create_jenkins_job_tool', 'JenkinsJobTool'] 