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

logger = logging.getLogger(__name__)

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
            self.server = jenkins.Jenkins(
                self.jenkins_url,
                username=self.username,
                password=self.api_token
            )
            user = self.server.get_whoami()
            version = self.server.get_version()
            logger.info(f"Connected to Jenkins {version} as {user['fullName']}")
        except Exception as e:
            logger.error(f"Failed to connect to Jenkins: {str(e)}")
            raise

    def trigger_build(self, parameters: Dict[str, Any]) -> int:
        """Trigger Jenkins build with parameters."""
        try:
            # Load parameter type information
            with open('/tmp/jenkins_config.json', 'r') as f:
                config = json.load(f)
            
            # Get parameter types from config
            param_types = config.get('parameters', {})
            
            # Unsanitize parameters before sending to Jenkins
            jenkins_params = self._unsanitize_parameters(parameters, param_types)
            
            logger.debug(f"Original parameters: {parameters}")
            logger.debug(f"Unsanitized parameters for Jenkins: {jenkins_params}")
            
            # Queue the build with unsanitized parameters
            queue_id = self.server.build_job(self.job_name, parameters=jenkins_params)
            
            # Get build number from queue
            while True:
                queue_item = self.server.get_queue_item(queue_id)
                if queue_item.get('executable'):
                    return queue_item['executable']['number']
                time.sleep(2)
        except Exception as e:
            logger.error(f"Failed to trigger build: {str(e)}")
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
        # Load configuration
        with open('/tmp/jenkins_config.json', 'r') as f:
            config = json.load(f)
        
        # Get parameters from environment variables
        parameters = get_parameters_from_env()
        
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
        print("🔌 Connecting to Jenkins...")
        runner.connect()
        
        # Trigger build
        print("🚀 Triggering build...")
        build_number = runner.trigger_build(parameters)
        print(f"📋 Build #{build_number} started")
        
        # Monitor build
        print("👀 Monitoring build progress...")
        status, url = runner.monitor_build(build_number)
        
        # Process result
        if status == 'SUCCESS':
            print(f"✅ Build completed successfully")
            print(f"🔗 Build URL: {url}")
            sys.exit(0)
        else:
            print(f"❌ Build failed with status: {status}")
            print(f"🔗 Build URL: {url}")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main() 