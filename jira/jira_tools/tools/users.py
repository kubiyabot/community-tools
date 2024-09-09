from .base import JiraTool, register_jira_tool
from kubiya_sdk.tools import Arg

user_get = JiraTool(
    name="user_get",
    description="Get JIRA user details",
    content="""
import os
from jira import JIRA

jira = JIRA(server=os.environ['JIRA_SERVER'], token_auth=os.environ['JIRA_OAUTH_TOKEN'])

user = jira.user(username)
print(f"User details: {user.__dict__}")
    """,
    args=[
        Arg(name="username", type="str", description="Username", required=True),
    ],
)

register_jira_tool(user_get)