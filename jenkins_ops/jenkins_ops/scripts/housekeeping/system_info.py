#!/usr/bin/env python3
import os
import sys
import logging
import requests
import json
from typing import Dict, Any

logger = logging.getLogger(__name__)

class JenkinsSystemMonitor:
    def __init__(self, jenkins_url: str, auth: tuple):
        self.jenkins_url = jenkins_url.rstrip('/')
        self.session = requests.Session()
        self.session.auth = auth
        self.session.headers.update({'Content-Type': 'application/json'})

    def get_system_info(self) -> Dict[str, Any]:
        """Get Jenkins system information and metrics."""
        try:
            # Get system info
            info_url = f"{self.jenkins_url}/api/json?depth=2"
            response = self.session.get(info_url)
            response.raise_for_status()
            system_info = response.json()

            # Get queue information
            queue_url = f"{self.jenkins_url}/queue/api/json"
            queue_response = self.session.get(queue_url)
            queue_response.raise_for_status()
            queue_info = queue_response.json()

            return {
                "success": True,
                "system_info": {
                    "version": system_info.get('systemInfo', {}).get('version', 'Unknown'),
                    "running_jobs": len(system_info.get('jobs', [])),
                    "queued_items": len(queue_info.get('items', [])),
                    "quiet_mode": system_info.get('quietingDown', False),
                    "slave_agents_port": system_info.get('slaveAgentPort', -1),
                    "useSecurity": system_info.get('useSecurity', True),
                    "nodes": {
                        "total": len(system_info.get('nodes', [])),
                        "online": sum(1 for n in system_info.get('nodes', []) if not n.get('offline', True))
                    }
                }
            }
        except Exception as e:
            logger.error(f"Failed to get system info: {str(e)}")
            return {"success": False, "message": str(e)}

    def get_metrics(self) -> Dict[str, Any]:
        """Get Jenkins metrics if metrics plugin is installed."""
        try:
            url = f"{self.jenkins_url}/metrics/api/json"
            response = self.session.get(url)
            response.raise_for_status()
            
            return {
                "success": True,
                "metrics": response.json()
            }
        except Exception as e:
            logger.error(f"Failed to get metrics (plugin might not be installed): {str(e)}")
            return {
                "success": False,
                "message": "Failed to get metrics. Metrics plugin might not be installed."
            }

def main():
    logging.basicConfig(level=logging.INFO)

    jenkins_url = os.environ.get('JENKINS_URL')
    username = os.environ.get('JENKINS_USERNAME')
    api_token = os.environ.get('JENKINS_API_TOKEN')
    action = os.environ.get('ACTION', 'info')

    if not all([jenkins_url, username, api_token]):
        logger.error("Missing required environment variables")
        sys.exit(1)

    monitor = JenkinsSystemMonitor(jenkins_url, auth=(username, api_token))

    if action == "info":
        result = monitor.get_system_info()
    elif action == "metrics":
        result = monitor.get_metrics()
    else:
        result = {"success": False, "message": f"Unknown action: {action}"}

    print(json.dumps(result, indent=2))
    sys.exit(0 if result['success'] else 1)

if __name__ == '__main__':
    main() 