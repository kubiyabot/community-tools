import logging
from kubiya_sdk.tools.registry import tool_registry
from .jenkins_job_tool import JenkinsJobTool
from .parser import JenkinsJobParser
from .config import DEFAULT_JENKINS_CONFIG
import json

logger = logging.getLogger(__name__)

# Initialize tools dictionary at module level
tools = {}

def initialize_tools():
    """Initialize and register Jenkins tools."""
    try:
        logger.info("Initializing Jenkins tools...")
        
        # Load configuration and create parser
        logger.info(f"Connecting to Jenkins server at {DEFAULT_JENKINS_CONFIG['jenkins_url']}...")
        parser = JenkinsJobParser(
            jenkins_url=DEFAULT_JENKINS_CONFIG['jenkins_url'],
            username=DEFAULT_JENKINS_CONFIG['auth']['username'],
            api_token="${JENKINS_API_TOKEN}"
        )

        # Get jobs from Jenkins server
        logger.info("Fetching Jenkins jobs...")
        jobs_info, warnings, errors = parser.get_jobs()
        
        if errors:
            error_msg = "\n- ".join(errors)
            logger.error(f"Errors during job discovery:\n- {error_msg}")
            if not jobs_info:
                raise Exception(
                    f"Failed to fetch any jobs from Jenkins server. Errors encountered:\n- {error_msg}\n"
                    "Please verify:\n"
                    f"1. Jenkins server is accessible at {DEFAULT_JENKINS_CONFIG['jenkins_url']}\n"
                    "2. Authentication credentials are correct\n"
                    "3. Jenkins API token is properly configured\n"
                    "4. Jenkins server has jobs configured"
                )
        
        if warnings:
            warning_msg = "\n- ".join(warnings)
            logger.warning(f"Warnings during job discovery:\n- {warning_msg}")

        if not jobs_info:
            raise Exception(
                "No Jenkins jobs were found on the server.\n"
                "Please verify:\n"
                "1. Jenkins server has jobs configured\n"
                "2. The configured user has permission to view jobs\n"
                "3. Jobs are not filtered by configuration"
            )

        # Create and register tools for each job
        for job_name, job_info in jobs_info.items():
            try:
                # Convert all parameter defaults to strings
                parameters = {}
                for param_name, param_config in job_info.get('parameters', {}).items():
                    param_config = param_config.copy()
                    if 'default' in param_config:
                        # Ensure default value is a string
                        if isinstance(param_config['default'], (dict, list)):
                            param_config['default'] = json.dumps(param_config['default'])
                        else:
                            param_config['default'] = str(param_config['default'])
                    parameters[param_name] = param_config

                tool_config = {
                    "name": f"jenkins_job_{job_name}",
                    "description": f"Execute Jenkins job: {job_name}\n{job_info.get('description', '')}",
                    "job_config": {
                        "name": job_name,
                        "parameters": parameters,
                        "auth": DEFAULT_JENKINS_CONFIG['auth']
                    },
                    "long_running": True,
                    "stream_logs": True,
                    "poll_interval": 30
                }

                # Create tool
                tool = JenkinsJobTool(**tool_config)
                tool.prepare()
                
                # Register tool
                tool_registry.register("jenkins", tool)
                tools[tool.name] = tool
                
                logger.info(f"Successfully registered tool for job: {job_name}")
                
            except Exception as e:
                logger.error(f"Failed to create tool for job {job_name}: {str(e)}")
                continue

        if not tools:
            raise Exception(
                "Failed to create any Jenkins tools.\n"
                "Jobs were found but tool creation failed.\n"
                "Please check the logs for specific error messages for each job."
            )

        logger.info(f"Successfully initialized {len(tools)} Jenkins tools")
        return list(tools.values())

    except Exception as e:
        logger.error(f"Failed to initialize Jenkins tools: {str(e)}")
        return []