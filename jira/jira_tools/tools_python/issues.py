import inspect
from typing import List

from kubiya_sdk.tools import Arg, FileSpec

from ..base import JiraPythonTool, register_jira_tool
from . import create_issue, basic_funcs, get_issue


class BaseCreationIssueTool(JiraPythonTool):
    def __init__(self, name: str, description: str, issue_type: str, extra_content: str = None,
                 extra_args: List[Arg] = None):
        if extra_args is None:
            extra_args = []
        content = f"""python /tmp/create_issue.py "{{{{ .project_key }}}}" "{{{{ .name }}}}" "{{{{ .description }}}}" {issue_type} "{{{{ .priority }}}}" "{{{{ .assignee_email }}}}" --label="{{{{ .label }}}}" {extra_content}"""
        args = [
            Arg(name="project_key", type="str", description="Jira project key", required=True),
            Arg(name="name", type="str", description=f"{issue_type} name", required=True),
            Arg(name="description", type="str", description=f"{issue_type} description", required=True),
            Arg(name="priority", type="str", description=f"{issue_type} priority can be Low, Medium, or High",
                required=False),
            Arg(name="assignee_email", type="str", description=f"{issue_type} assignee user", required=False),
            Arg(name="label", default="", type="str", description=f"{issue_type} label", required=False),
            # TODO: understand why label make rerun sometimes
        ]
        args.extend(extra_args)

        super().__init__(
            name=name,
            description=description,
            content=content,
            args=args,
            with_files=[
                FileSpec(
                    destination="/tmp/create_issue.py",
                    content=inspect.getsource(create_issue),
                ),
                FileSpec(
                    destination="/tmp/basic_funcs.py",
                    content=inspect.getsource(basic_funcs),
                )
            ])

create_epic_tool = BaseCreationIssueTool(
    name="create_epic",
    description="Create new jira epic",
    issue_type="Epic"
)

create_task_tool = BaseCreationIssueTool(
    name="create_epic",
    description="Create new jira Task",
    issue_type="Task"
)

create_bug_tool = BaseCreationIssueTool(
    name="create_bug_tool",
    description="Create new jira bug",
    issue_type="Bug"
)

create_story_tool = BaseCreationIssueTool(
    name="create_story_tool",
    description="Create new jira story",
    issue_type="Story"
)

create_subtask_tool = BaseCreationIssueTool(
    name="create_sub_task_tool",
    description="Create new jira Sub-task",
    issue_type="Sub-task",
    extra_args=[
        Arg(name="parent_id", default="", type="str", description=f"Task parent id, like: JRA-817", required=True)
    ],
    extra_content=f"""--parent_id="{{{{ .parent_id }}}}" """
)

get_issue_tool = JiraPythonTool(
    name="get_issue_information",
    description="Get Jira issue information",
    content="""python /tmp/get_issue.py "{{ .issue_key }}" """,
    args=[
        Arg(name="issue_key", default="", type="str", description=f"Issue id, like: JRA-817", required=True)
    ],
    with_files=[
        FileSpec(
            destination="/tmp/get_issue.py",
            content=inspect.getsource(get_issue),
        ),
        FileSpec(
            destination="/tmp/basic_funcs.py",
            content=inspect.getsource(basic_funcs),
        )
    ])


register_jira_tool(create_task_tool)
register_jira_tool(create_subtask_tool)
register_jira_tool(create_bug_tool)
register_jira_tool(create_epic_tool)
register_jira_tool(create_story_tool)
register_jira_tool(get_issue_tool)
