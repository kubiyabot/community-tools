from kubiya_sdk.tools.models import Tool, Arg, FileSpec
import json

OKTA_ICON_URL = "https://www.okta.com/sites/default/files/Okta_Logo_BrightBlue_Medium.png"

class OktaTool(Tool):
    def __init__(self, name, description, action, args, env=[], long_running=False, mermaid_diagram=None):
        env = ["KUBIYA_USER_EMAIL", *env]
        secrets = ["OKTA_API_TOKEN", "OKTA_ORG_URL"]
        
        arg_names_json = json.dumps([arg.name for arg in args])
        
        script_content = f'''
import os
import sys
import json
import logging
import requests
from urllib.parse import urlparse
from typing import Optional, Dict, List, Union

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OktaClient:
    def __init__(self, org_url: str, token: str):
        # Ensure the org_url has a scheme and is properly formatted
        if not urlparse(org_url).scheme:
            org_url = "https://" + org_url
        if not org_url.endswith('.okta.com'):
            org_url = org_url + ".okta.com"
        
        self.base_url = org_url.rstrip('/')
        logger.info("Initializing Okta client with base URL: %s", self.base_url)
        
        self.headers = {{
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': 'SSWS ' + token
        }}

    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, params: Optional[Dict] = None) -> Union[Dict, List, None]:
        url = self.base_url + (endpoint if endpoint.startswith('/') else '/' + endpoint)
        logger.debug("Making request to: %s", url)
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                json=data,
                params=params
            )
            response.raise_for_status()
            return response.json() if response.text else None
        except requests.exceptions.HTTPError as e:
            error_detail = e.response.json() if e.response and e.response.text else {{'error': str(e)}}
            logger.error("HTTP Error: %s", error_detail)
            raise Exception(f"Okta API Error: {{error_detail}}")
        except requests.exceptions.RequestException as e:
            logger.error("Request Error: %s", str(e))
            raise Exception(f"Request Error: {{str(e)}}")

    def list_groups(self, query: Optional[str] = None, filter: Optional[str] = None, after: Optional[str] = None, limit: Optional[int] = None) -> List[Dict]:
        params = {{'q': query}} if query else {{}}
        if filter:
            params['filter'] = filter
        if after:
            params['after'] = after
        if limit:
            params['limit'] = limit
        return self._make_request('GET', '/api/v1/groups', params=params)

    def create_group(self, name: str, description: Optional[str] = None, skip_naming_conflict_resolution: bool = False) -> Dict:
        data = {{
            'profile': {{
                'name': name,
                'description': description
            }}
        }}
        params = {{'skipNamingConflictResolution': skip_naming_conflict_resolution}}
        return self._make_request('POST', '/api/v1/groups', data=data, params=params)

    def get_group(self, group_id: str) -> Dict:
        return self._make_request('GET', f'/api/v1/groups/{{group_id}}')

    def update_group(self, group_id: str, name: str, description: Optional[str] = None) -> Dict:
        data = {{
            'profile': {{
                'name': name,
                'description': description
            }}
        }}
        return self._make_request('PUT', f'/api/v1/groups/{{group_id}}', data=data)

    def delete_group(self, group_id: str) -> None:
        return self._make_request('DELETE', f'/api/v1/groups/{{group_id}}')

    def list_group_members(self, group_id: str, after: Optional[str] = None, limit: Optional[int] = None) -> List[Dict]:
        params = {{}}
        if after:
            params['after'] = after
        if limit:
            params['limit'] = limit
        return self._make_request('GET', f'/api/v1/groups/{{group_id}}/users', params=params)

    def add_user_to_group(self, group_id: str, user_id: str) -> None:
        return self._make_request('PUT', f'/api/v1/groups/{{group_id}}/users/{{user_id}}')

    def remove_user_from_group(self, group_id: str, user_id: str) -> None:
        return self._make_request('DELETE', f'/api/v1/groups/{{group_id}}/users/{{user_id}}')

    def search_users(self, query: Optional[str] = None, filter: Optional[str] = None, search: Optional[str] = None, 
                    limit: Optional[int] = None, after: Optional[str] = None) -> List[Dict]:
        """Search users with advanced query options."""
        params = {{}}
        if query:
            params['q'] = query
        if filter:
            params['filter'] = filter
        if search:
            params['search'] = search
        if limit:
            params['limit'] = min(int(limit), 200)
        if after:
            params['after'] = after
            
        try:
            return self._make_request('GET', '/api/v1/users', params=params)
        except Exception as e:
            logger.error("Error searching users: %s", str(e))
            return []

    def get_user(self, user_id: str, fields: Optional[List[str]] = None) -> Optional[Dict]:
        """Get user by ID with optional field selection."""
        params = {{}}
        if fields and isinstance(fields, (list, tuple)):
            params['fields'] = ','.join(fields)
            
        try:
            return self._make_request('GET', f'/api/v1/users/{{user_id}}', params=params)
        except Exception as e:
            logger.error("Error getting user: %s", str(e))
            return None

def get_okta_client() -> OktaClient:
    org_url = os.environ['OKTA_ORG_URL']
    token = os.environ['OKTA_API_TOKEN']
    
    if not org_url:
        raise ValueError("OKTA_ORG_URL environment variable is required")
        
    org_url = org_url.strip()
    logger.info("Creating Okta client with org URL: %s", org_url)
    return OktaClient(org_url, token)

def find_group_by_name(client: OktaClient, group_name: str) -> Optional[Dict]:
    logger.info("Searching for group: %s", group_name)
    try:
        groups = client.list_groups(query=group_name)
        for group in groups:
            if group['profile']['name'].lower() == group_name.lower():
                return group
        return None
    except Exception as e:
        logger.error("Error searching for group: %s", str(e))
        return None

def execute_okta_action(action: str, operation: str, **kwargs) -> Dict:
    client = get_okta_client()
    logger.info("Executing Okta action: %s", action)
    logger.info("Action parameters: %s", kwargs)

    try:
        if action == "users":
            if operation == "get_user":
                fields = kwargs.get('fields', '').split(',') if kwargs.get('fields') else None
                result = client.get_user(kwargs['identifier'], fields=fields)
                if result:
                    return {{"success": True, "user": result}}
                return {{"success": False, "error": f"User not found: {{kwargs['identifier']}}"}}
                
            elif operation == "search_users":
                result = client.search_users(
                    query=kwargs.get('query'),
                    filter=kwargs.get('filter'),
                    search=kwargs.get('search'),
                    limit=kwargs.get('limit'),
                    after=kwargs.get('after')
                )
                return {{"success": True, "users": result}}
                
            elif operation == "list_users":
                result = client.search_users(
                    limit=kwargs.get('limit'),
                    after=kwargs.get('after')
                )
                return {{"success": True, "users": result}}
            else:
                return {{"success": False, "error": f"Unknown operation: {{operation}}"}}

        elif action == "groups":
            if operation == "list_groups":
                result = client.list_groups(
                    query=kwargs.get('query'),
                    filter=kwargs.get('filter'),
                    after=kwargs.get('after'),
                    limit=kwargs.get('limit')
                )
                return {{"success": True, "groups": result}}

            elif operation == "create_group":
                result = client.create_group(
                    name=kwargs['name'],
                    description=kwargs.get('description'),
                    skip_naming_conflict_resolution=kwargs.get('skip_naming_conflict_resolution', False)
                )
                return {{"success": True, "group": result}}

            elif operation == "update_group":
                result = client.update_group(
                    group_id=kwargs['group_id'],
                    name=kwargs['name'],
                    description=kwargs.get('description')
                )
                return {{"success": True, "group": result}}

            elif operation == "delete_group":
                client.delete_group(kwargs['group_id'])
                return {{"success": True, "message": f"Group {{kwargs['group_id']}} deleted"}}

            elif operation == "get_group":
                result = client.get_group(kwargs['group_id'])
                return {{"success": True, "group": result}}

            elif operation == "list_members":
                result = client.list_group_members(
                    group_id=kwargs['group_id'],
                    after=kwargs.get('after'),
                    limit=kwargs.get('limit')
                )
                return {{"success": True, "members": result}}

            elif operation == "add_member":
                group = find_group_by_name(client, kwargs['group_name'])
                if not group:
                    return {{"success": False, "error": f"Group {{kwargs['group_name']}} not found"}}
                client.add_user_to_group(group['id'], kwargs['user_id'])
                return {{"success": True, "message": f"User {{kwargs['user_id']}} added to group {{kwargs['group_name']}}"}}

            elif operation == "remove_member":
                group = find_group_by_name(client, kwargs['group_name'])
                if not group:
                    return {{"success": False, "error": f"Group {{kwargs['group_name']}} not found"}}
                client.remove_user_from_group(group['id'], kwargs['user_id'])
                return {{"success": True, "message": f"User {{kwargs['user_id']}} removed from group {{kwargs['group_name']}}"}}

            else:
                return {{"success": False, "error": f"Unknown operation: {{operation}}"}}
        else:
            return {{"success": False, "error": f"Unknown action: {{action}}"}}

    except Exception as e:
        logger.error("Error executing action: %s", str(e))
        return {{"success": False, "error": str(e)}}

if __name__ == "__main__":
    token = os.environ.get("OKTA_API_TOKEN")
    org_url = os.environ.get("OKTA_ORG_URL")
    
    if not token or not org_url:
        logger.error("Missing required environment variables")
        print(json.dumps({{"success": False, "error": "Missing required environment variables"}}))
        sys.exit(1)

    logger.info("Starting Okta action execution...")
    arg_names = {arg_names_json}
    args = {{}}
    for arg in arg_names:
        if arg in os.environ:
            args[arg] = os.environ[arg]
    
    result = execute_okta_action("{action}", "{name}", **args)
    logger.info("Okta action execution completed")
    print(json.dumps(result))
'''
        super().__init__(
            name=name,
            description=description,
            icon_url=OKTA_ICON_URL,
            type="docker",
            image="python:3.11-slim",
            on_build="pip install requests",
            content="python /tmp/script.py",
            args=args,
            env=env,
            secrets=secrets,
            long_running=long_running,
            mermaid=mermaid_diagram,
            with_files=[
                FileSpec(
                    destination="/tmp/script.py",
                    content=script_content,
                )
            ],
        )