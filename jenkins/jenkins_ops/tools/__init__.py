import logging
from kubiya_sdk.tools.registry import tool_registry
from .jenkins_job_tool import JenkinsJobTool
from .parser import JenkinsJobParser
from .config import DEFAULT_JENKINS_CONFIG
from typing import Dict, Any
import json

logger = logging.getLogger(__name__)

# Default configuration values
DEFAULT_CONFIG = {
    "stream_logs": True,
    "poll_interval": 10,  # seconds
    "sync_all": True,
    "include": [],
    "exclude": [],
}

def get_jenkins_config() -> Dict[str, Any]:
    """Get Jenkins configuration from dynamic config."""
    EXAMPLE_CONFIG = """{
        "jenkins": {
            "url": "http://jenkins.example.com:8080",  # Required: Jenkins server URL
            "username": "admin",  # Required: Jenkins username
            "password": "your-jenkins-api-token",  # Required: Jenkins API token or password
            "jobs": {
                "sync_all": True,  # Optional: set to False to use include/exclude lists
                "include": ["job1", "job2"],  # Optional: list of jobs to include if sync_all is False
                "exclude": ["test-job"] # Optional: list of jobs to exclude
            },
            "defaults": {  # Optional: default settings for all jobs
                "stream_logs": True,
                "poll_interval": 10
            }
        }
    }"""

    try:
        config = tool_registry.dynamic_config
    except Exception as e:
        raise ValueError(
            f"Failed to get dynamic configuration: {str(e)}\nExpected configuration structure:\n"  + EXAMPLE_CONFIG
        )

    if not config:
        raise ValueError(
            "No dynamic configuration provided. Expected configuration structure:\n" + EXAMPLE_CONFIG
        )

    # Get Jenkins configuration
    jenkins_config = config.get('jenkins', {})
    if not jenkins_config:
        raise ValueError(
            "No Jenkins configuration found in dynamic config. Expected configuration structure:\n" + EXAMPLE_CONFIG
        )

    # Required fields
    required_fields = ['url', 'username', 'password']
    missing_fields = [field for field in required_fields if not jenkins_config.get(field)]
    if missing_fields:
        raise ValueError(
            f"Missing required Jenkins configuration fields: {', '.join(missing_fields)}\n"
            "Example of a valid configuration:\n"
            f"{json.dumps(EXAMPLE_CONFIG, indent=2)}"
        )

    # Build configuration with defaults
    ret = {
        "jenkins_url": jenkins_config['url'],
        "auth": {
            "username": jenkins_config['username'],
            "password": jenkins_config['password']
        },
        "jobs": {
            "sync_all": jenkins_config.get('jobs', {}).get('sync_all', True),
            "include": jenkins_config.get('jobs', {}).get('include', []),
            "exclude": jenkins_config.get('jobs', {}).get('exclude', []),
        },
        "defaults": {
            "stream_logs": jenkins_config.get('defaults', {}).get('stream_logs', DEFAULT_CONFIG['stream_logs']),
            "poll_interval": jenkins_config.get('defaults', {}).get('poll_interval', DEFAULT_CONFIG['poll_interval'])
        }
    }
    print("used_config=", ret)
    return ret

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
            example_config = {
                "jenkins": {
                    "url": "http://jenkins.example.com:8080",
                    "username": "admin",
                    "password": "your-jenkins-api-token"
                }
            }
            raise ValueError(
                "Jenkins authentication password is required but not provided in configuration.\n"
                "Example of a valid configuration:\n"
                f"{json.dumps(example_config, indent=2)}"
            )
        
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
            job_include_filter = config['jobs'].get('include') if not config['jobs'].get('sync_all') else None
            job_exclude_filter = config['jobs'].get('exclude') if not config['jobs'].get('sync_all') else None
            jobs_info, warnings, errors = parser.get_jobs(job_include_filter=job_include_filter, job_exclude_filter=job_exclude_filter)
        except Exception as jobs_error:
            example_config = {
                "jenkins": {
                    "url": "http://jenkins.example.com:8080",
                    "username": "admin",
                    "password": "your-jenkins-api-token",
                    "sync_all": False,  # Set to false to use include/exclude lists
                    "include": ["job1", "job2"],  # List of jobs to include
                    "exclude": ["test-job"],  # List of jobs to exclude
                    "defaults": {  # Optional: default settings for all jobs
                        "stream_logs": True,
                        "poll_interval": 10
                    }
                }
            }
            raise ValueError(
                f"Failed to fetch Jenkins jobs: {str(jobs_error)}\n"
                "If you're trying to filter specific jobs, ensure your configuration includes job filters like this:\n"
                f"{json.dumps(example_config, indent=2)}"
            )

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
        "name": job_name.lower().replace('-', '_').replace(' ', '_'),
        "description": job_info.get('description', f"Execute Jenkins job: {job_name}"),
        "job_config": {
            "name": job_name,
            "parameters": job_info.get('parameters', {}),
            "auth": config['auth']
        },
        "long_running": False,
        "stream_logs": config.get('defaults', DEFAULT_CONFIG)['stream_logs'],
        "poll_interval": config.get('defaults', DEFAULT_CONFIG)['poll_interval']
    }

    tool = JenkinsJobTool(**tool_config)
    tool.prepare()
    return tool

# Initialize tools dictionary
tools = {}