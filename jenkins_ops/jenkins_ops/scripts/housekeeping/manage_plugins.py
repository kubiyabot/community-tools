#!/usr/bin/env python3
import os
import sys
import logging
import requests
import json
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class JenkinsPluginManager:
    def __init__(self, jenkins_url: str, auth: tuple):
        self.jenkins_url = jenkins_url.rstrip('/')
        self.session = requests.Session()
        self.session.auth = auth
        self.session.headers.update({'Content-Type': 'application/json'})

    def list_plugins(self) -> Dict[str, Any]:
        """List all installed plugins with their versions and update status."""
        try:
            url = f"{self.jenkins_url}/pluginManager/api/json?depth=1"
            response = self.session.get(url)
            response.raise_for_status()
            plugins = response.json().get('plugins', [])

            plugin_list = [{
                "shortName": p["shortName"],
                "version": p["version"],
                "hasUpdate": p.get("hasUpdate", False),
                "enabled": p.get("enabled", True),
                "active": p.get("active", True)
            } for p in plugins]

            return {
                "success": True,
                "plugins": plugin_list,
                "total_count": len(plugin_list),
                "updates_available": sum(1 for p in plugin_list if p["hasUpdate"])
            }

        except Exception as e:
            logger.error(f"Failed to list plugins: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to list plugins: {str(e)}",
                "plugins": []
            }

    def update_all_plugins(self) -> Dict[str, Any]:
        """Update all plugins that have updates available."""
        try:
            url = f"{self.jenkins_url}/pluginManager/installNecessaryPlugins"
            response = self.session.post(url)
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "message": "Plugin updates initiated successfully."
                }
            else:
                return {
                    "success": False,
                    "message": f"Failed to initiate plugin updates: {response.text}"
                }

        except Exception as e:
            logger.error(f"Failed to update plugins: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to update plugins: {str(e)}"
            }

    def update_plugin(self, plugin_name: str) -> Dict[str, Any]:
        """Update a specific plugin."""
        try:
            url = f"{self.jenkins_url}/pluginManager/install"
            data = {
                "dynamicLoad": True,
                "plugins": [{"name": plugin_name, "version": "latest"}]
            }
            
            response = self.session.post(url, json=data)
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "message": f"Plugin {plugin_name} update initiated successfully."
                }
            else:
                return {
                    "success": False,
                    "message": f"Failed to update plugin {plugin_name}: {response.text}"
                }

        except Exception as e:
            logger.error(f"Failed to update plugin {plugin_name}: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to update plugin {plugin_name}: {str(e)}"
            }

def main():
    # Configure logging
    logging.basicConfig(level=logging.INFO)

    # Get environment variables
    jenkins_url = os.environ.get('JENKINS_URL')
    username = os.environ.get('JENKINS_USERNAME')
    api_token = os.environ.get('JENKINS_API_TOKEN')
    action = os.environ.get('ACTION', 'list')
    plugin_name = os.environ.get('PLUGIN_NAME')

    # Validate required environment variables
    if not all([jenkins_url, username, api_token]):
        logger.error("Missing required environment variables")
        sys.exit(1)

    # Initialize plugin manager
    manager = JenkinsPluginManager(jenkins_url, auth=(username, api_token))

    # Execute requested action
    if action == "list":
        result = manager.list_plugins()
    elif action == "update_all":
        result = manager.update_all_plugins()
    elif action == "update_plugin":
        if not plugin_name:
            result = {
                "success": False,
                "message": "Plugin name is required for update_plugin action"
            }
        else:
            result = manager.update_plugin(plugin_name)
    else:
        result = {
            "success": False,
            "message": f"Unknown action: {action}"
        }

    # Print result and exit
    print(json.dumps(result, indent=2))
    sys.exit(0 if result['success'] else 1)

if __name__ == '__main__':
    main() 