import inspect

from kubiya_sdk.tools import Arg, FileSpec

from ..base import JiraPythonTool, register_jira_tool
from . import create_issue, basic_funcs


class BaseCreationTool(JiraPythonTool):
    def __init__(self, name, description, issue_type, content=None, extra_args=None):
        if extra_args is None:
            extra_args = []
        content = f"""python /tmp/create_issue.py "{{{{ .project_key }}}}" "{{{{ .name }}}}" "{{{{ .description }}}}" {issue_type} "{{{{ .priority }}}}" "{{{{ .assignee_email }}}}" --label="{{{{ .label }}}} {content}"""
        args = [
                Arg(name="project_key", type="str", description="Jira project key", required=True),
                Arg(name="name", type="str", description=f"{issue_type} name", required=True),
                Arg(name="description", type="str", description=f"{issue_type} description", required=True),
                Arg(name="priority", type="str", description=f"{issue_type} priority can be Low, Medium, or High",
                    required=False),
                Arg(name="assignee_email", type="str", description=f"{issue_type} assignee user", required=False),
                Arg(name="label", default="", type="str", description=f"{issue_type} label", required=False), # TODO: understand why label make rerun sometimes
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


create_epic_tool = BaseCreationTool(
    name="create_epic",
    description="Create new jira epic",
    issue_type="Epic"
)

create_task_tool = BaseCreationTool(
    name="create_epic",
    description="Create new jira epic",
    issue_type="Task"
)

create_bug_tool = BaseCreationTool(
    name="create_bug_tool",
    description="Create new jira bug",
    issue_type="Bug"
)

create_story_tool = BaseCreationTool(
    name="create_story_tool",
    description="Create new jira story",
    issue_type="Story"
)

create_subtask_tool = BaseCreationTool(
    name="create_sub_task_tool",
    description="Create new jira Sub-task",
    issue_type="Sub-task",
    extra_args=[Arg(name="parent_id", default="", type="str", description=f"Task parent id, like: JRA-817", required=True)],
)

register_jira_tool(create_task_tool)
register_jira_tool(create_subtask_tool)
register_jira_tool(create_bug_tool)
register_jira_tool(create_epic_tool)
register_jira_tool(create_story_tool)
