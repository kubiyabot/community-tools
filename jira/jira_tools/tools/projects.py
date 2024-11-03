from jira.jira_tools.base import JiraTool, register_jira_tool
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

# Add the following functions:

board_get = JiraTool(
    name="board_get",
    description="Get JIRA board details",
    content="""
import os
from jira import JIRA

jira = JIRA(server=os.environ['JIRA_SERVER'], token_auth=os.environ['JIRA_OAUTH_TOKEN'])

board = jira.board(board_id)
print(f"Board details: {board.__dict__}")
    """,
    args=[
        Arg(name="board_id", type="int", description="Board ID", required=True),
    ],
)

board_list = JiraTool(
    name="board_list",
    description="List JIRA boards",
    content="""
import os
from jira import JIRA

jira = JIRA(server=os.environ['JIRA_SERVER'], token_auth=os.environ['JIRA_OAUTH_TOKEN'])

boards = jira.boards()
for board in boards:
    print(f"Board: {board.id} - {board.name}")
    """,
    args=[],
)

sprint_get = JiraTool(
    name="sprint_get",
    description="Get JIRA sprint details",
    content="""
import os
from jira import JIRA

jira = JIRA(server=os.environ['JIRA_SERVER'], token_auth=os.environ['JIRA_OAUTH_TOKEN'])

sprint = jira.sprint(sprint_id)
print(f"Sprint details: {sprint.__dict__}")
    """,
    args=[
        Arg(name="sprint_id", type="int", description="Sprint ID", required=True),
    ],
)

sprint_create = JiraTool(
    name="sprint_create",
    description="Create a new JIRA sprint",
    content="""
import os
from jira import JIRA

jira = JIRA(server=os.environ['JIRA_SERVER'], token_auth=os.environ['JIRA_OAUTH_TOKEN'])

new_sprint = jira.create_sprint(name, board_id, startDate, endDate)
print(f"Created sprint: {new_sprint.id}")
    """,
    args=[
        Arg(name="name", type="str", description="Sprint name", required=True),
        Arg(name="board_id", type="int", description="Board ID", required=True),
        Arg(name="startDate", type="str", description="Start date (YYYY-MM-DD)", required=True),
        Arg(name="endDate", type="str", description="End date (YYYY-MM-DD)", required=True),
    ],
)

sprint_update = JiraTool(
    name="sprint_update",
    description="Update an existing JIRA sprint",
    content="""
import os
from jira import JIRA

jira = JIRA(server=os.environ['JIRA_SERVER'], token_auth=os.environ['JIRA_OAUTH_TOKEN'])

updated_sprint = jira.update_sprint(sprint_id, name=name, startDate=startDate, endDate=endDate)
print(f"Updated sprint: {updated_sprint.id}")
    """,
    args=[
        Arg(name="sprint_id", type="int", description="Sprint ID", required=True),
        Arg(name="name", type="str", description="New sprint name", required=False),
        Arg(name="startDate", type="str", description="New start date (YYYY-MM-DD)", required=False),
        Arg(name="endDate", type="str", description="New end date (YYYY-MM-DD)", required=False),
    ],
)

# Register new tools
register_jira_tool(project_list)
register_jira_tool(project_get)
register_jira_tool(board_get)
register_jira_tool(board_list)
register_jira_tool(sprint_get)
register_jira_tool(sprint_create)
register_jira_tool(sprint_update)