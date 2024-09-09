from .base import JiraTool, register_jira_tool
from kubiya_sdk.tools import Arg

project_get = JiraTool(
    name="project_get",
    description="Get JIRA project details",
    content="""
import os
from jira import JIRA

jira = JIRA(server=os.environ['JIRA_SERVER'], token_auth=os.environ['JIRA_OAUTH_TOKEN'])

project = jira.project(project_key)
print(f"Project details: {project.__dict__}")
    """,
    args=[
        Arg(name="project_key", type="str", description="Project key", required=True),
    ],
)

project_list = JiraTool(
    name="project_list",
    description="List JIRA projects",
    content="""
import os
from jira import JIRA

jira = JIRA(server=os.environ['JIRA_SERVER'], token_auth=os.environ['JIRA_OAUTH_TOKEN'])

projects = jira.projects()
for project in projects:
    print(f"Project: {project.key} - {project.name}")
    """,
    args=[],
)

register_jira_tool(project_get)
register_jira_tool(project_list)