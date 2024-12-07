import logging
import os
from typing import List
from kubiya_sdk.tools.registry import tool_registry
from ..parser import JenkinsJobParser
from .jenkins_job_tool import JenkinsJobTool
from ..scripts.config_loader import get_jenkins_config

logger = logging.getLogger(__name__)

def create_jenkins_job_tool(job_config: dict, long_running: bool = False) -> JenkinsJobTool:
    """Create a Jenkins job tool from configuration."""
    
    # Generate tool name with self_service prefix
    base_name = job_config['name'].lower().replace(' ', '_')
    tool_name = f"self_service_jenkins_{base_name}"
    
    # Create tool description
    description = (
        f"Execute Jenkins job: {job_config['name']}\n"
        f"{job_config.get('description', '')}\n"
        f"URL: {job_config['url']}"
    )

    return JenkinsJobTool(
        name=tool_name,
        description=description,
        job_config=job_config,
        long_running=long_running,
        type="docker",
        image="python:3.9-alpine"
    )

def initialize_tools() -> List[JenkinsJobTool]:
    """Initialize all Jenkins job tools."""
    tools = []
    
    try:
        # Load Jenkins configuration
        config = get_jenkins_config()
        if not config:
            logger.error("Failed to load Jenkins configuration")
            return tools

        # Get Jenkins credentials
        jenkins_token = os.environ.get(config['auth']['password_env'])
        if not jenkins_token:
            logger.error(f"Environment variable {config['auth']['password_env']} not set")
            return tools

        # Initialize parser
        parser = JenkinsJobParser(
            jenkins_url=config['jenkins_url'],
            username=config['auth']['username'],
            password=jenkins_token
        )

        # Get job filter based on configuration
        job_filter = None
        if not config.get('jobs', {}).get('sync_all', False):
            include_jobs = set(config.get('jobs', {}).get('include', []))
            exclude_jobs = set(config.get('jobs', {}).get('exclude', []))
            if include_jobs:
                job_filter = list(include_jobs - exclude_jobs)

        # Get jobs from Jenkins
        jobs_info, warnings, errors = parser.get_jobs(job_filter)

        # Log any warnings or errors
        for warning in warnings:
            logger.warning(warning)
        for error in errors:
            logger.error(error)

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
                logger.error(f"Failed to create tool for job {job_name}: {str(e)}")
                continue

    except Exception as e:
        logger.error(f"Failed to initialize tools: {str(e)}")

    return tools

__all__ = ['initialize_tools', 'create_jenkins_job_tool', 'JenkinsJobTool'] 