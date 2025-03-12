#!/usr/bin/env python3
try:
    import jenkins
except ImportError:
    print("WARN: jenkins module not found,this could be OK if you are just syncing (discovering) jobs against the Jenkins server")
    pass
import time
import json
import os
import sys
import logging
from typing import Dict, Any, Optional, Tuple

# Configure logging to stdout with immediate flushing
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout,
    force=True
)

# Ensure all print statements are flushed immediately
sys.stdout.reconfigure(line_buffering=True)

logger = logging.getLogger(__name__)

def log_and_print(message: str, level: str = "INFO") -> None:
    """Log a message and print it to stdout."""
    print(message, flush=True)
    if level == "INFO":
        logger.info(message)
    elif level == "ERROR":
        logger.error(message)
    elif level == "DEBUG":
        logger.debug(message)
    elif level == "WARNING":
        logger.warning(message)

class JenkinsJobRunner:
    """Handles Jenkins job execution and monitoring."""
    
    def __init__(
        self,
        jenkins_url: str,
        username: str,
        api_token: str,
        job_name: str,
        stream_logs: bool = True,
        poll_interval: int = 30
    ):
        log_and_print(f"🔧 Initializing Jenkins runner for job: {job_name}")
        log_and_print(f"Jenkins URL: {jenkins_url}", "DEBUG")
        log_and_print(f"Username: {username}", "DEBUG")
        
        self.jenkins_url = jenkins_url
        self.username = username
        self.api_token = api_token
        self.job_name = job_name
        self.stream_logs = stream_logs
        self.poll_interval = poll_interval
        self.server = None

    def _unsanitize_parameters(self, parameters: Dict[str, Any], param_types: Dict[str, Dict[str, str]]) -> Dict[str, Any]:
        """Convert parameters back to their original names and types for Jenkins API."""
        unsanitized = {}
        
        for param_name, value in parameters.items():
            # Get the original parameter info
            param_info = param_types.get(param_name, {})
            original_name = param_info.get('original_name', param_name)
            param_type = param_info.get('type', 'str')
            
            # Convert value based on type
            if param_type == 'bool':
                # Convert string 'true'/'false' back to boolean for Jenkins
                value = str(value).lower() == 'true'
            elif param_type == 'str':
                # Ensure string type
                value = str(value)
            
            # Use original parameter name when sending to Jenkins
            unsanitized[original_name] = value
            
        return unsanitized

    def connect(self) -> None:
        """Establish connection to Jenkins server."""
        try:
            log_and_print("🔌 Attempting to connect to Jenkins...")
            self.server = jenkins.Jenkins(
                self.jenkins_url,
                username=self.username,
                password=self.api_token
            )
            user = self.server.get_whoami()
            version = self.server.get_version()
            log_and_print(f"✅ Connected to Jenkins {version} as {user['fullName']}")
        except Exception as e:
            log_and_print(f"❌ Failed to connect to Jenkins: {str(e)}", "ERROR")
            raise

    def _prepare_parameters_for_jenkins(self, parameters: Dict[str, Any], param_types: Dict[str, Dict[str, str]]) -> Dict[str, Any]:
        """Convert parameters to format expected by Jenkins."""
        jenkins_params = {}
        
        for param_name, value in parameters.items():
            # Get parameter info
            param_info = param_types.get(param_name, {})
            original_name = param_info.get('original_name', param_name)
            param_type = param_info.get('type', 'str')
            
            # Convert value based on type
            if param_type == 'bool':
                # Jenkins expects boolean as true/false string
                jenkins_params[original_name] = str(value).lower()
            elif param_type == 'str':
                if isinstance(value, (dict, list)):
                    # For complex types, convert back to string as Jenkins expects
                    jenkins_params[original_name] = json.dumps(value)
                else:
                    jenkins_params[original_name] = str(value)
            else:
                # For other types, pass as string
                jenkins_params[original_name] = str(value)
        
        return jenkins_params

    def trigger_build(self, parameters: Dict[str, Any]) -> int:
        """Trigger Jenkins build with parameters."""
        try:
            log_and_print(f"🚀 Triggering build for job: {self.job_name}")
            
            # Load parameter type information
            log_and_print("📝 Loading parameter configuration...", "DEBUG")
            with open('/tmp/jenkins_config.json', 'r') as f:
                config = json.load(f)
            
            # Get parameter types from config
            param_types = config.get('parameters', {})
            log_and_print(f"Parameters configuration: {json.dumps(param_types, indent=2)}", "DEBUG")
            
            # Convert parameters to Jenkins format
            jenkins_params = self._prepare_parameters_for_jenkins(parameters, param_types)
            log_and_print(f"Prepared parameters: {json.dumps(jenkins_params, indent=2)}", "DEBUG")
            
            # Queue the build with prepared parameters
            log_and_print("⏳ Queuing build with Jenkins...")
            queue_id = self.server.build_job(self.job_name, parameters=jenkins_params)
            log_and_print(f"✅ Build queued with ID: {queue_id}")
            
            # Get build number from queue
            log_and_print("⏳ Waiting for build number...")
            while True:
                queue_item = self.server.get_queue_item(queue_id)
                if queue_item.get('executable'):
                    build_number = queue_item['executable']['number']
                    log_and_print(f"📋 Build number received: {build_number}")
                    return build_number
                log_and_print("Still waiting for build to start...", "DEBUG")
                time.sleep(2)
        except Exception as e:
            log_and_print(f"❌ Failed to trigger build: {str(e)}", "ERROR")
            raise

    def get_build_logs(self, build_number: int, start_line: int = 0) -> Optional[str]:
        """Get incremental build logs."""
        try:
            return self.server.get_build_console_output(self.job_name, build_number)
        except Exception as e:
            logger.warning(f"Failed to get build logs: {str(e)}")
            return None

    def monitor_build(self, build_number: int) -> Tuple[str, str]:
        """Monitor build progress."""
        try:
            last_line = 0
            while True:
                build_info = self.server.get_build_info(self.job_name, build_number)
                status = build_info.get('result')
                
                # Stream logs if enabled
                if self.stream_logs:
                    logs = self.get_build_logs(build_number, last_line)
                    if logs:
                        print(logs, end='')
                        last_line = len(logs.splitlines())
                
                if status:
                    return status, build_info.get('url', '')
                
                time.sleep(self.poll_interval)
        except Exception as e:
            logger.error(f"Failed to monitor build: {str(e)}")
            raise

def get_parameters_from_env() -> Dict[str, Any]:
    """Get job parameters from environment variables and convert to appropriate types."""
    parameters = {}
    
    # Load job config to get parameter information
    with open('/tmp/jenkins_config.json', 'r') as f:
        config = json.load(f)
    
    # Get parameters from environment variables
    for param_name, param_info in config.get('parameters', {}).items():
        env_value = os.environ.get(param_name)
        if env_value is not None:
            param_type = param_info.get('type', 'str')
            
            try:
                # Convert value based on parameter type
                if param_type == 'bool':
                    parameters[param_name] = str(env_value).lower() == 'true'
                elif param_type == 'str':
                    # Handle JSON strings for complex types
                    if env_value.startswith('{') or env_value.startswith('['):
                        try:
                            parameters[param_name] = json.loads(env_value)
                        except json.JSONDecodeError:
                            parameters[param_name] = env_value
                    else:
                        parameters[param_name] = env_value
                else:
                    # Default to string for unknown types
                    parameters[param_name] = str(env_value)
                    
            except Exception as e:
                logger.warning(f"Error converting parameter {param_name}: {str(e)}")
                parameters[param_name] = env_value
    
    return parameters

def main():
    """Main execution function."""
    try:
        log_and_print("🚀 Starting Jenkins job runner")
        
        # Load configuration
        log_and_print("📝 Loading configuration...")
        with open('/tmp/jenkins_config.json', 'r') as f:
            config = json.load(f)
            log_and_print(f"Configuration loaded: {json.dumps(config, indent=2)}", "DEBUG")
        
        # Get parameters from environment variables
        log_and_print("🔍 Getting parameters from environment...")
        parameters = get_parameters_from_env()
        log_and_print(f"Parameters: {json.dumps(parameters, indent=2)}", "DEBUG")
        
        # Initialize runner
        runner = JenkinsJobRunner(
            jenkins_url=os.environ['JENKINS_URL'],
            username=config['username'],
            api_token=os.environ['JENKINS_API_TOKEN'],
            job_name=config['job_name'],
            stream_logs=config.get('stream_logs', True),
            poll_interval=config.get('poll_interval', 30)
        )
        
        # Connect to Jenkins
        runner.connect()
        
        # Trigger build
        build_number = runner.trigger_build(parameters)
        
        # Monitor build
        log_and_print(f"👀 Monitoring build #{build_number}...")
        status, url = runner.monitor_build(build_number)
        log_and_print(f"Build completed with status: {status}")
        
        # Process result
        if status == 'SUCCESS':
            log_and_print(f"✅ Build completed successfully")
            log_and_print(f"🔗 Build URL: {url}")
            sys.exit(0)
        else:
            log_and_print(f"❌ Build failed with status: {status}")
            log_and_print(f"🔗 Build URL: {url}")
            sys.exit(1)
            
    except Exception as e:
        log_and_print(f"❌ Error: {str(e)}", "ERROR")
        sys.exit(1)

if __name__ == '__main__':
    main() 