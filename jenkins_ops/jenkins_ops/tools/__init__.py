import logging
from kubiya_sdk.tools.registry import tool_registry
from .jenkins_job_tool import JenkinsJobTool
from .parser import JenkinsJobParser
from .config import DEFAULT_JENKINS_CONFIG
import re

logger = logging.getLogger(__name__)

# Initialize tools dictionary at module level
tools = {}

def _sanitize_tool_name(name: str, max_length: int = 50) -> str:
    """
    Sanitize and normalize tool names.
    
    Args:
        name: The original job name
        max_length: Maximum allowed length for the name (default: 50)
    
    Returns:
        Sanitized and normalized name suitable for a tool
    """
    if not name:
        return ""
    
    # Remove any path-like components (for jobs in folders)
    name = name.split('/')[-1]
    
    # Replace spaces, dashes, and other special characters with underscores
    sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', name)
    
    # Replace multiple underscores with a single underscore
    sanitized = re.sub(r'_+', '_', sanitized)
    
    # Remove leading/trailing underscores
    sanitized = sanitized.strip('_')
    
    # Convert to lowercase for consistency
    sanitized = sanitized.lower()
    
    # Truncate if too long, but keep it meaningful
    if len(sanitized) > max_length:
        # Keep the first and last parts if we need to truncate
        parts = sanitized.split('_')
        if len(parts) > 2:
            # Keep first and last part
            sanitized = f"{parts[0]}_{parts[-1]}"
        else:
            # Just truncate
            sanitized = sanitized[:max_length]
    
    return f"jenkins_job_{sanitized}"

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
            logger.warning(f"Warnings during job fetching:\n- {warning_msg}")

        # Create and register tools for each job
        for job_name, job_info in jobs_info.items():
            try:
                # Sanitize the tool name
                tool_name = _sanitize_tool_name(job_name)
                logger.debug(f"Creating tool '{tool_name}' for job '{job_name}'")

                tool_config = {
                    "name": tool_name,
                    "description": f"Execute Jenkins job: {job_name}\n{job_info.get('description', '')}",
                    "job_config": {
                        "name": job_name,  # Keep original job name for Jenkins
                        "parameters": job_info.get('parameters', {}),
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
                tools[tool_name] = tool
                
                logger.info(f"Successfully registered tool '{tool_name}' for job '{job_name}'")
                
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