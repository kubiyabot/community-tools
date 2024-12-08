from kubiya_sdk.tools.registry import tool_registry
import logging
import json
from pathlib import Path
from typing import List
from .jenkins_job_tool import JenkinsJobTool

logger = logging.getLogger(__name__)

def load_jenkins_config() -> dict:
    """Load Jenkins configuration from config file."""
    try:
        config_path = Path(__file__).parent.parent / 'scripts' / 'configs' / 'jenkins_config.json'
        with open(config_path) as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load Jenkins config: {str(e)}")
        return {}

def initialize_tools() -> List[JenkinsJobTool]:
    """Initialize and register Jenkins tools with Kubiya."""
    try:
        # Load Jenkins configuration
        jenkins_config = load_jenkins_config()
        if not jenkins_config:
            logger.error("No Jenkins configuration found")
            return []

        # Initialize parser to get jobs from server
        logger.info("Initializing Jenkins parser...")
        from .parser import JenkinsJobParser
        
        parser = JenkinsJobParser(
            jenkins_url=jenkins_config['jenkins_url'],
            username=jenkins_config['auth']['username'],
            api_token="${JENKINS_API_TOKEN}"  # Will be resolved at runtime
        )

        # Get jobs from Jenkins server
        logger.info("Fetching Jenkins jobs...")
        jobs_info, warnings, errors = parser.get_jobs(
            job_filter=jenkins_config.get('jobs', {}).get('include', [])
        )

        if errors:
            for error in errors:
                logger.error(f"Parser error: {error}")
            if not jobs_info:
                return []

        if warnings:
            for warning in warnings:
                logger.warning(f"Parser warning: {warning}")

        # Create and register tools for each job
        registered_tools = []
        excluded_jobs = jenkins_config.get('jobs', {}).get('exclude', [])

        for job_name, job_info in jobs_info.items():
            try:
                # Skip excluded jobs
                if job_name in excluded_jobs:
                    logger.info(f"Skipping excluded job: {job_name}")
                    continue

                # Create tool configuration
                tool_config = {
                    "name": f"jenkins_job_{job_name}",
                    "description": f"Execute Jenkins job: {job_name}\n{job_info.get('description', '')}",
                    "job_config": {
                        "name": job_name,
                        "parameters": job_info.get('parameters', {}),
                        "auth": {
                            "username": jenkins_config['auth']['username']
                        }
                    },
                    "long_running": True,
                    "stream_logs": True,
                    "poll_interval": 30
                }

                # Create and initialize the tool
                tool = JenkinsJobTool(**tool_config)
                tool.prepare()  # Initialize args and other configurations

                # Register tool with Kubiya
                tool_registry.register("jenkins", tool)
                registered_tools.append(tool)
                
                logger.info(f"Successfully registered tool for job: {job_name}")

            except Exception as e:
                logger.error(f"Failed to create tool for job {job_name}: {str(e)}")
                continue

        logger.info(f"Successfully registered {len(registered_tools)} Jenkins job tools")
        return registered_tools

    except Exception as e:
        logger.error(f"Failed to initialize Jenkins tools: {str(e)}")
        return []
    