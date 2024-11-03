import inspect
from kubiya_sdk.tools import Arg, FileSpec

from ..base import JiraPythonTool, register_jira_tool
from .. import basic_funcs

create_issue = JiraPythonTool(
    name="create_issue",
    description="Create new jira issue",
    content="""
    import os
    print(os.system('ls'))

    import requests
    import json
    
    from basic_funcs import get_jira_cloud_id, get_jira_basic_headers, ATLASSIAN_JIRA_API_URL
    
    cloud_id = get_jira_cloud_id()
    headers = get_jira_basic_headers()

    payload = {
        "fields": {
            "project": {
                "key": "{{ .project_key }}"
            },
            "summary": "{{ .name }}",
            "description": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "text": "{{ .description }}",
                                "type": "text"
                            }
                        ]
                    }
                ]
            },
            "issuetype": {
                "name": "{{ .issue_type }}"
            },
        }
    }
    priority, assignee_id, labels = "{{ .priority }}", "{{ .assignee_id }}", "{{ .labels }}"
    if priority:
        payload["fields"]["priority"] = {
            "name": priority
    }
    if assignee_id:
        payload["fields"]["assignee"] = {
            "id": assignee_id
    }
    if labels:
        payload["fields"]["labels"] = labels  
        
    post_issue_url = f"{ATLASSIAN_JIRA_API_URL}/{cloud_id}/rest/api/3/issue"
    
    try:
        response = requests.post(post_issue_url, headers=headers, data=json.dumps(payload))
        print(response.json())
    except Exception as e:
        print(f"Failed to create issue: {e}")     
    .....
    """,
    args=[
        Arg(name="project_key", type="str", description="Jira project key", required=True),
        Arg(name="name", type="str", description="Issue name", required=True),
        Arg(name="issue_type", type="str", description="Issue type, such as Task, Sub-Task, Epic, Bug etc.", required=True),
        Arg(name="description", type="str", description="Issue description", required=True),
        Arg(name="priority", type="str", description="Issue priority can be Low Medium or High", required=False),
        Arg(name="assignee_email", type="str", description="Issue assignee user", required=False),
        # Arg(name="labels", type="array", description="Issue labels", required=False),
    ],
    # with_files=[
    #     FileSpec(
    #         destination="/tmp/basic_funcs.py",
    #         content=inspect.getsource(basic_funcs),
    #     )]

)

register_jira_tool(create_issue)
