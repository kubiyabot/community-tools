#!/usr/bin/env python3
import jenkins
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
            # Queue the build
            queue_id = self.server.build_job(self.job_name, parameters=parameters)
            
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
    
    # Load job config to get parameter names
    with open('/tmp/jenkins_config.json', 'r') as f:
        config = json.load(f)
    
    # Get parameters from environment variables
    for param_name in config.get('parameters', []):
        env_value = os.environ.get(param_name)
        if env_value is not None:
            # All values come as strings, try to convert based on content
            try:
                # Try JSON first for complex types
                if env_value.startswith('{') or env_value.startswith('['):
                    parameters[param_name] = json.loads(env_value)
                    continue
                
                # Handle boolean values
                if env_value.lower() in ('true', 'false'):
                    parameters[param_name] = env_value.lower() == 'true'
                    continue
                
                # Handle numeric values
                if env_value.isdigit():
                    parameters[param_name] = int(env_value)
                    continue
                if env_value.replace('.', '', 1).isdigit():
                    parameters[param_name] = float(env_value)
                    continue
                
                # Default to string
                parameters[param_name] = env_value
                
            except json.JSONDecodeError:
                # If JSON parsing fails, use raw string
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