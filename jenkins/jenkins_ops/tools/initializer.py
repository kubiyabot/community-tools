__all__ = ['initialize_tools']

from kubiya_workflow_sdk.tools.registry import tool_registry
import logging
import json
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)

class JenkinsConfigError(Exception):
    """Custom exception for Jenkins configuration errors."""
    pass

def load_jenkins_config() -> dict:
    """Load Jenkins configuration from config file."""
    try:
        logger.info("Loading Jenkins configuration...")
        config_path = Path(__file__).parent.parent / 'scripts' / 'configs' / 'jenkins_config.json'
        if not config_path.exists():
            raise JenkinsConfigError(
                f"Jenkins configuration file not found at: {config_path}\n"
                "Please ensure jenkins_config.json exists in the correct location."
            )

        with open(config_path) as f:
            config = json.load(f)

        # Validate required configuration fields
        required_fields = {
            'jenkins_url': "Jenkins server URL",
            'auth': "Authentication configuration",
        }
        
        missing_fields = [
            f"{field} ({desc})" 
            for field, desc in required_fields.items() 
            if field not in config
        ]
        
        if missing_fields:
            raise JenkinsConfigError(
                "Missing required configuration fields:\n- " + 
                "\n- ".join(missing_fields)
            )

        return config
    except json.JSONDecodeError as e:
        raise JenkinsConfigError(
            f"Invalid JSON in jenkins_config.json: {str(e)}\n"
            "Please verify the configuration file format."
        )
    except Exception as e:
        if isinstance(e, JenkinsConfigError):
            raise
        raise JenkinsConfigError(f"Failed to load Jenkins config: {str(e)}")

def validate_jobs_config(config: dict) -> Optional[str]:
    """Validate jobs configuration and return warning message if needed."""
    jobs_config = config.get('jobs', {})
    
    if not jobs_config.get('sync_all') and not jobs_config.get('include'):
        return (
            "No jobs specified for synchronization. "
            "Set 'sync_all: true' or specify jobs in 'include' list."
        )
    return None

def initialize_tools() -> List:
    """Initialize and register Jenkins tools with Kubiya."""
    try:
        # Move imports inside the function to avoid circular imports
        from .jenkins_job_tool import JenkinsJobTool
        from .parser import JenkinsJobParser

        # Load and validate Jenkins configuration
        jenkins_config = load_jenkins_config()

        # Check jobs configuration
        jobs_warning = validate_jobs_config(jenkins_config)
        if jobs_warning:
            logger.warning(jobs_warning)

        # Initialize parser to get jobs from server
        logger.info("Initializing Jenkins parser...")
        parser = JenkinsJobParser(
            jenkins_url=jenkins_config['jenkins_url'],
            username=jenkins_config['auth']['username'],
            api_token="${JENKINS_API_TOKEN}"  # Will be resolved at runtime
        )

        # Get jobs from Jenkins server
        logger.info("Fetching Jenkins jobs...")
        jobs_info, warnings, errors = parser.get_jobs(
            job_filter=jenkins_config.get('jobs', {}).get('include', [])
            if not jenkins_config.get('jobs', {}).get('sync_all')
            else None
        )

        if errors:
            error_details = "\n- ".join(errors)
            logger.error(f"Encountered errors while fetching jobs:\n- {error_details}")
            if not jobs_info:
                raise JenkinsConfigError(
                    "Failed to fetch any jobs from Jenkins server.\n"
                    f"Errors encountered:\n- {error_details}\n"
                    "Please verify:\n"
                    "1. Jenkins server is accessible\n"
                    "2. Authentication credentials are correct\n"
                    "3. Specified jobs exist and are accessible"
                )

        if warnings:
            warning_details = "\n- ".join(warnings)
            logger.warning(f"Warnings during job fetching:\n- {warning_details}")

        # Create and register tools for each job
        registered_tools = []
        excluded_jobs = jenkins_config.get('jobs', {}).get('exclude', [])
        processed_jobs = 0
        skipped_jobs = 0

        for job_name, job_info in jobs_info.items():
            try:
                # Skip excluded jobs
                if job_name in excluded_jobs:
                    logger.info(f"Skipping excluded job: {job_name}")
                    skipped_jobs += 1
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
                processed_jobs += 1
                
                logger.info(f"Successfully registered tool for job: {job_name}")

            except Exception as e:
                logger.error(f"Failed to create tool for job {job_name}: {str(e)}")
                continue

        # Provide detailed summary
        summary = (
            f"Jenkins tools initialization complete:\n"
            f"- Total jobs found: {len(jobs_info)}\n"
            f"- Successfully registered: {processed_jobs}\n"
            f"- Skipped (excluded): {skipped_jobs}\n"
            f"- Failed to register: {len(jobs_info) - processed_jobs - skipped_jobs}"
        )
        logger.info(summary)

        if not registered_tools:
            logger.error("No Jenkins tools were registered.")
            raise JenkinsConfigError(
                "No Jenkins tools were registered.\n"
                "Please verify:\n"
                "1. Jenkins jobs are correctly specified in configuration\n"
                "2. Included jobs exist and are accessible\n"
                "3. Jobs have valid configurations"
            )

        return registered_tools

    except JenkinsConfigError as e:
        logger.error(f"Jenkins configuration error: {str(e)}")
        raise JenkinsConfigError(
            "Failed to initialize Jenkins tools. See logs for details.\n"
            f"Error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error during Jenkins tools initialization: {str(e)}")
        raise JenkinsConfigError(
            "Failed to initialize Jenkins tools. See logs for details.\n"
            f"Error: {str(e)}"
        )
     