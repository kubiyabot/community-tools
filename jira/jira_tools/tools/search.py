# from ..base import JiraTool, register_jira_tool
# from kubiya_sdk.tools import Arg
#
# search_issues = JiraTool(
#     name="search_issues",
#     description="Search JIRA issues",
#     content="""
# import os
# from jira import JIRA
#
# jira = JIRA(server=os.environ['JIRA_SERVER'], token_auth=os.environ['JIRA_OAUTH_TOKEN'])
#
# issues = jira.search_issues(jql_str)
# for issue in issues:
#     print(f"Issue: {issue.key} - {issue.fields.summary}")
#     """,
#     args=[
#         Arg(name="jql_str", type="str", description="JQL search string", required=True),
#     ],
# )
#
# register_jira_tool(search_issues)
