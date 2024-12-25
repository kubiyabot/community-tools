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
            "password_env": jenkins_config.get('token_env', 'JENKINS_API_TOKEN')
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
        config = get_jenkins_config()
        logger.info(f"Using Jenkins server at {config['jenkins_url']}")
        
        # Create parser
        parser = JenkinsJobParser(
            jenkins_url=config['jenkins_url'],
            username=config['auth']['username'],
            api_token="${" + config['auth']['password_env'] + "}"
        )

        # Get jobs from Jenkins server
        logger.info("Fetching Jenkins jobs...")
        jobs_info, warnings, errors = parser.get_jobs(
            include_jobs=config['jobs'].get('include'),
            exclude_jobs=config['jobs'].get('exclude'),
            sync_all=config['jobs'].get('sync_all', True)
        )

        # Handle errors and warnings
        if errors:
            error_msg = "\n- ".join(errors)
            logger.error(f"Errors during job discovery:\n- {error_msg}")
            if not jobs_info:
                raise ValueError(f"Failed to fetch any jobs. Errors:\n- {error_msg}")

        if warnings:
            warning_msg = "\n- ".join(warnings)
            logger.warning(f"Warnings during job fetching:\n- {warning_msg}")

        # Create and register tools
        tools = []
        for job_name, job_info in jobs_info.items():
            try:
                tool = create_jenkins_tool(job_name, job_info, config)
                if tool:
                    tool_registry.register("jenkins", tool)
                    tools.append(tool)
                    logger.info(f"Registered tool for job: {job_name}")
            except Exception as e:
                logger.error(f"Failed to create tool for job {job_name}: {str(e)}")

        if not tools:
            raise ValueError("No tools were created from Jenkins jobs")

        logger.info(f"Successfully initialized {len(tools)} Jenkins tools")
        return tools

    except Exception as e:
        logger.error(f"Failed to initialize Jenkins tools: {str(e)}")
        raise

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