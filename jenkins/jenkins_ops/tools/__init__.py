import logging
from kubiya_sdk.tools.registry import tool_registry
from .jenkins_job_tool import JenkinsJobTool
from .parser import JenkinsJobParser
from .config import DEFAULT_JENKINS_CONFIG
from typing import Dict, Any

logger = logging.getLogger(__name__)

def get_jenkins_config() -> Dict[str, Any]:
    """Get Jenkins configuration from dynamic config."""
    config = tool_registry.dynamic_config
    if not config:
        raise ValueError("No dynamic configuration provided")

    # Get Jenkins configuration
    jenkins_config = config.get('jenkins', {})
    if not jenkins_config:
        raise ValueError("No Jenkins configuration found in dynamic config")

    # Required fields
    required_fields = ['url']
    missing_fields = [field for field in required_fields if field not in jenkins_config]
    if missing_fields:
        raise ValueError(f"Missing required Jenkins configuration fields: {', '.join(missing_fields)}")

    # Build configuration with defaults
    return {
        "jenkins_url": jenkins_config.get('url'),
        "auth": {
            "username": jenkins_config.get('username', 'admin'),
            "password": jenkins_config.get('password')
        },
        "jobs": {
            "sync_all": jenkins_config.get('sync_all', True),
            "include": jenkins_config.get('include_jobs', []),
            "exclude": jenkins_config.get('exclude_jobs', [])
        },
        "defaults": {
            "stream_logs": jenkins_config.get('stream_logs', True),
            "poll_interval": jenkins_config.get('poll_interval', 30),
            "long_running_threshold": jenkins_config.get('long_running_threshold', 300)
        }
    }

def initialize_tools():
    """Initialize and register Jenkins tools."""
    try:
        logger.info("Initializing Jenkins tools...")
        
        # Get configuration from dynamic config
        try:
            config = get_jenkins_config()
        except ValueError as config_error:
            raise ValueError(f"Failed to get Jenkins configuration: {str(config_error)}")
            
        logger.info(f"Using Jenkins server at {config['jenkins_url']}")
        
        # Validate auth configuration
        if not config['auth'].get('password'):
            raise ValueError("Jenkins authentication password is required but not provided in configuration")
        
        # Create parser
        try:
            parser = JenkinsJobParser(
                jenkins_url=config['jenkins_url'],
                username=config['auth']['username'],
                api_token=config['auth']['password']
            )
        except Exception as parser_error:
            raise ValueError(f"Failed to create Jenkins parser: {str(parser_error)}")

        # Get jobs from Jenkins server
        logger.info("Fetching Jenkins jobs...")
        try:
            job_filter = config['jobs'].get('include') if not config['jobs'].get('sync_all') else None
            jobs_info, warnings, errors = parser.get_jobs(job_filter=job_filter)
        except Exception as jobs_error:
            raise ValueError(f"Failed to fetch Jenkins jobs: {str(jobs_error)}")

        # Handle errors and warnings
        if errors:
            error_msg = "\n- ".join(errors)
            logger.error(f"Errors during job discovery:\n- {error_msg}")
            if not jobs_info:
                raise ValueError(f"Failed to fetch any jobs from Jenkins server. Errors encountered:\n- {error_msg}")

        if warnings:
            warning_msg = "\n- ".join(warnings)
            logger.warning(f"Warnings during job fetching:\n- {warning_msg}")

        # Create and register tools
        tools = []
        failed_jobs = []
        for job_name, job_info in jobs_info.items():
            try:
                tool = create_jenkins_tool(job_name, job_info, config)
                if tool:
                    tool_registry.register("jenkins", tool)
                    tools.append(tool)
                    logger.info(f"Registered tool for job: {job_name}")
            except Exception as e:
                error_msg = f"Failed to create tool for job {job_name}: {str(e)}"
                logger.error(error_msg)
                failed_jobs.append({"job": job_name, "error": str(e)})

        if not tools:
            if failed_jobs:
                error_details = "\n- ".join([f"{job['job']}: {job['error']}" for job in failed_jobs])
                raise ValueError(f"Failed to create any Jenkins tools. Errors for each job:\n- {error_details}")
            else:
                raise ValueError("No Jenkins jobs were found to create tools from")

        if failed_jobs:
            logger.warning(f"Successfully created {len(tools)} tools, but {len(failed_jobs)} jobs failed")
        else:
            logger.info(f"Successfully initialized all {len(tools)} Jenkins tools")
            
        return tools

    except Exception as e:
        logger.error(f"Failed to initialize Jenkins tools: {str(e)}")
        raise ValueError(f"Jenkins tools initialization failed: {str(e)}")

def create_jenkins_tool(job_name: str, job_info: Dict[str, Any], config: Dict[str, Any]) -> JenkinsJobTool:
    """Create a Jenkins tool for a specific job."""
    tool_config = {
        "name": f"jenkins_job_{job_name.lower().replace('-', '_')}",
        "description": job_info.get('description', f"Execute Jenkins job: {job_name}"),
        "job_config": {
            "name": job_name,
            "parameters": job_info.get('parameters', {}),
            "auth": config['auth']
        },
        "long_running": True,
        "stream_logs": config['defaults']['stream_logs'],
        "poll_interval": config['defaults']['poll_interval']
    }

    tool = JenkinsJobTool(**tool_config)
    tool.prepare()
    return tool

# Initialize tools dictionary
tools = {}