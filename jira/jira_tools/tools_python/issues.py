import inspect

from kubiya_sdk.tools import Arg, FileSpec

from ..base import JiraPythonTool, register_jira_tool
from . import create_issue, basic_funcs

class BaseCreationTool(JiraPythonTool):
    def __init__(self, name, description, issue_type):
        super().__init__(
            name=name,
            description=description,
            content=f"""
python /tmp/create_issue.py "{{{{ .project_key }}}}" "{{{{ .name }}}}" "{{{{ .description }}}}" {issue_type} "{{{{ .priority }}}}" "{{{{ .assignee_email }}}}" --label="{{{{ .label }}}}"
            """,
            args=[
                Arg(name="project_key", type="str", description="Jira project key", required=True),
                Arg(name="name", type="str", description=f"{issue_type} name", required=True),
                Arg(name="description", type="str", description=f"{issue_type} description", required=True),
                Arg(name="priority", type="str", description=f"{issue_type} priority can be Low, Medium, or High",
                    required=False),
                Arg(name="assignee_email", type="str", description=f"{issue_type} assignee user", required=False),
                Arg(name="label", default="", type="str", description=f"{issue_type} label", required=False),
            ],
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


create_task_tool = JiraPythonTool(
    name="create_task",
    description="Create new jira task",
    content="""
    python /tmp/create_issue.py "{{ .project_key }}" "{{ .name }}" "{{ .description }}" Task "{{ .priority }}" "{{ .assignee_email }}" --label="{{ .label }}"
    """,

    args=[
        Arg(name="project_key", type="str", description="Jira project key", required=True),
        Arg(name="name", type="str", description="Task name", required=True),
        Arg(name="description", type="str", description="Task description", required=True),
        Arg(name="priority", type="str", description="Task priority can be Low Medium or High", required=False),
        Arg(name="assignee_email", type="str", description="Task assignee user", required=False),
        Arg(name="label", default="", type="str", description="Task label", required=False),
    ],
    with_files=[
        FileSpec(
            destination="/tmp/create_issue.py",
            content=inspect.getsource(create_issue),
        ),
        FileSpec(
            destination="/tmp/basic_funcs.py",
            content=inspect.getsource(basic_funcs),
        )
    ]

)

create_bug_tool = JiraPythonTool(
    name="create_bug_tool",
    description="Create new jira bug",
    content="""
    python /tmp/create_issue.py "{{ .project_key }}" "{{ .name }}" "{{ .description }}" Bug "{{ .priority }}" "{{ .assignee_email }}" --label="{{ .label }}"
    """,

    args=[
        Arg(name="project_key", type="str", description="Jira project key", required=True),
        Arg(name="name", type="str", description="Bug name", required=True),
        Arg(name="description", type="str", description="Bug description", required=True),
        Arg(name="priority", type="str", description="Bug priority can be Low Medium or High", required=False),
        Arg(name="assignee_email", type="str", description="Bug assignee user", required=False),
        Arg(name="label", default="", type="str", description="Bug label", required=False),
    ],
    with_files=[
        FileSpec(
            destination="/tmp/create_issue.py",
            content=inspect.getsource(create_issue),
        ),
        FileSpec(
            destination="/tmp/basic_funcs.py",
            content=inspect.getsource(basic_funcs),
        )
    ]

)

create_epic_tool = BaseCreationTool(
    name="create_epic",
    description="Create new jira epic",
    issue_type="Epic"
)

register_jira_tool(create_task_tool)
register_jira_tool(create_bug_tool)
register_jira_tool(create_epic_tool)
