from .base import JiraTool, register_jira_tool
from kubiya_sdk.tools import Arg

issue_create = JiraTool(
    name="issue_create",
    description="Create a new JIRA issue",
    content="""
import os
from jira import JIRA

jira = JIRA(server=os.environ['JIRA_SERVER'], token_auth=os.environ['JIRA_OAUTH_TOKEN'])

issue_dict = {
    'project': {'key': project_key},
    'summary': summary,
    'description': description,
    'issuetype': {'name': issue_type},
}

new_issue = jira.create_issue(fields=issue_dict)
print(f"Created issue: {new_issue.key}")
    """,
    args=[
        Arg(name="project_key", type="str", description="Project key", required=True),
        Arg(name="summary", type="str", description="Issue summary", required=True),
        Arg(name="description", type="str", description="Issue description", required=True),
        Arg(name="issue_type", type="str", description="Issue type", required=True),
    ],
)

issue_update = JiraTool(
    name="issue_update",
    description="Update an existing JIRA issue",
    content="""
import os
from jira import JIRA

jira = JIRA(server=os.environ['JIRA_SERVER'], token_auth=os.environ['JIRA_OAUTH_TOKEN'])

issue = jira.issue(issue_key)
issue.update(fields=fields)
print(f"Updated issue: {issue_key}")
    """,
    args=[
        Arg(name="issue_key", type="str", description="Issue key", required=True),
        Arg(name="fields", type="dict", description="Fields to update", required=True),
    ],
)

issue_get = JiraTool(
    name="issue_get",
    description="Get JIRA issue details",
    content="""
import os
from jira import JIRA

jira = JIRA(server=os.environ['JIRA_SERVER'], token_auth=os.environ['JIRA_OAUTH_TOKEN'])

issue = jira.issue(issue_key)
print(f"Issue details: {issue.fields.__dict__}")
    """,
    args=[
        Arg(name="issue_key", type="str", description="Issue key", required=True),
    ],
)

issue_delete = JiraTool(
    name="issue_delete",
    description="Delete a JIRA issue",
    content="""
import os
from jira import JIRA

jira = JIRA(server=os.environ['JIRA_SERVER'], token_auth=os.environ['JIRA_OAUTH_TOKEN'])

jira.delete_issue(issue_key)
print(f"Deleted issue: {issue_key}")
    """,
    args=[
        Arg(name="issue_key", type="str", description="Issue key", required=True),
    ],
)

issue_assign = JiraTool(
    name="issue_assign",
    description="Assign a JIRA issue to a user",
    content="""
import os
from jira import JIRA

jira = JIRA(server=os.environ['JIRA_SERVER'], token_auth=os.environ['JIRA_OAUTH_TOKEN'])

issue = jira.issue(issue_key)
issue.update(assignee={'name': assignee})
print(f"Assigned issue {issue_key} to {assignee}")
    """,
    args=[
        Arg(name="issue_key", type="str", description="Issue key", required=True),
        Arg(name="assignee", type="str", description="Assignee username", required=True),
    ],
)

issue_add_comment = JiraTool(
    name="issue_add_comment",
    description="Add a comment to a JIRA issue",
    content="""
import os
from jira import JIRA

jira = JIRA(server=os.environ['JIRA_SERVER'], token_auth=os.environ['JIRA_OAUTH_TOKEN'])

comment = jira.add_comment(issue_key, body)
print(f"Added comment to issue {issue_key}: {comment.id}")
    """,
    args=[
        Arg(name="issue_key", type="str", description="Issue key", required=True),
        Arg(name="body", type="str", description="Comment body", required=True),
    ],
)

issue_transition = JiraTool(
    name="issue_transition",
    description="Transition a JIRA issue to a new status",
    content="""
import os
from jira import JIRA

jira = JIRA(server=os.environ['JIRA_SERVER'], token_auth=os.environ['JIRA_OAUTH_TOKEN'])

issue = jira.issue(issue_key)
jira.transition_issue(issue, transition_id)
print(f"Transitioned issue {issue_key} to new status")
    """,
    args=[
        Arg(name="issue_key", type="str", description="Issue key", required=True),
        Arg(name="transition_id", type="str", description="Transition ID", required=True),
    ],
)

register_jira_tool(issue_create)
register_jira_tool(issue_update)
register_jira_tool(issue_get)
register_jira_tool(issue_delete)
register_jira_tool(issue_assign)
register_jira_tool(issue_add_comment)
register_jira_tool(issue_transition)