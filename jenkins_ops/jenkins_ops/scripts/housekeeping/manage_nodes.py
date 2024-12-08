#!/usr/bin/env python3
import os
import sys
import logging
import requests
import json
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class JenkinsNodeManager:
    def __init__(self, jenkins_url: str, auth: tuple):
        self.jenkins_url = jenkins_url.rstrip('/')
        self.session = requests.Session()
        self.session.auth = auth
        self.session.headers.update({'Content-Type': 'application/json'})

    def list_nodes(self) -> Dict[str, Any]:
        """List all Jenkins nodes with their status."""
        try:
            url = f"{self.jenkins_url}/computer/api/json?depth=2"
            response = self.session.get(url)
            response.raise_for_status()
            computers = response.json().get('computer', [])

            node_list = [{
                "name": node["displayName"],
                "offline": node["offline"],
                "temporarilyOffline": node.get("temporarilyOffline", False),
                "executors": len(node.get("executors", [])),
                "labels": node.get("assignedLabels", []),
                "monitorData": node.get("monitorData", {}),
            } for node in computers]

            return {
                "success": True,
                "nodes": node_list,
                "total_nodes": len(node_list),
                "offline_nodes": sum(1 for n in node_list if n["offline"])
            }
        except Exception as e:
            logger.error(f"Failed to list nodes: {str(e)}")
            return {"success": False, "message": str(e)}

    def toggle_node(self, node_name: str, action: str) -> Dict[str, Any]:
        """Toggle node online/offline status."""
        try:
            if action not in ["online", "offline"]:
                return {"success": False, "message": "Invalid action. Use 'online' or 'offline'"}

            # Get current status
            url = f"{self.jenkins_url}/computer/{node_name}/api/json"
            response = self.session.get(url)
            response.raise_for_status()
            current_status = response.json()

            if action == "offline" and not current_status.get("offline"):
                url = f"{self.jenkins_url}/computer/{node_name}/toggleOffline"
                response = self.session.post(url)
                message = f"Node {node_name} marked offline"
            elif action == "online" and current_status.get("offline"):
                url = f"{self.jenkins_url}/computer/{node_name}/toggleOffline"
                response = self.session.post(url)
                message = f"Node {node_name} marked online"
            else:
                message = f"Node {node_name} already in desired state ({action})"

            return {"success": True, "message": message}
        except Exception as e:
            logger.error(f"Failed to toggle node {node_name}: {str(e)}")
            return {"success": False, "message": str(e)}

def main():
    logging.basicConfig(level=logging.INFO)

    jenkins_url = os.environ.get('JENKINS_URL')
    username = os.environ.get('JENKINS_USERNAME')
    api_token = os.environ.get('JENKINS_API_TOKEN')
    action = os.environ.get('ACTION', 'list')
    node_name = os.environ.get('NODE_NAME')
    node_state = os.environ.get('NODE_STATE')

    if not all([jenkins_url, username, api_token]):
        logger.error("Missing required environment variables")
        sys.exit(1)

    manager = JenkinsNodeManager(jenkins_url, auth=(username, api_token))

    if action == "list":
        result = manager.list_nodes()
    elif action == "toggle":
        if not all([node_name, node_state]):
            result = {
                "success": False,
                "message": "NODE_NAME and NODE_STATE required for toggle action"
            }
        else:
            result = manager.toggle_node(node_name, node_state)
    else:
        result = {"success": False, "message": f"Unknown action: {action}"}

    print(json.dumps(result, indent=2))
    sys.exit(0 if result['success'] else 1)

if __name__ == '__main__':
    main() 