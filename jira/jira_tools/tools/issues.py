import inspect
from typing import List
from kubiya_sdk.tools import Arg, FileSpec
from ..base import JiraPythonTool, register_jira_tool
from . import create_issue, basic_funcs, view_issue, list_issues, create_issue_comment, update_issue_status, assign_issue, sprint_ops


class BaseCreationIssueTool(JiraPythonTool):
    def __init__(self, name: str, issue_type: str, extra_content: str = "",
                 extra_args: List[Arg] = None):
        if extra_args is None:
            extra_args = []
        description = f"Create new jira {issue_type}"
        content = f"""python /tmp/create_issue.py "{{{{ .project_key }}}}" "{{{{ .name }}}}" "{{{{ .description }}}}" {issue_type} --assignee_email="{{{{ .assignee_email }}}}" --label="{{{{ .label }}}}" {extra_content}"""
        args = [
            Arg(name="project_key", type="str", description="Jira project key", required=True),
            Arg(name="name", type="str", description=f"{issue_type} name", required=True),
            Arg(name="description", type="str", description=f"{issue_type} description", required=True),
            Arg(name="assignee_email", type="str", description=f"{issue_type} assignee user", required=False),
            Arg(name="label", default="", type="str", description=f"{issue_type} label", required=False),
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
    issue_type="Epic"
)

create_task_tool = BaseCreationIssueTool(
    name="create_task",
    issue_type="Task"
)

create_bug_tool = BaseCreationIssueTool(
    name="create_bug_tool",
    issue_type="Bug"
)

create_story_tool = BaseCreationIssueTool(
    name="create_story_tool",
    issue_type="Story"
)

create_subtask_tool = BaseCreationIssueTool(
    name="create_sub_task_tool",
    issue_type="Sub-task",
    extra_args=[
        Arg(name="parent_id", default="", type="str", description=f"Task parent id, like: JRA-817", required=True)
    ],
    extra_content=f"""--parent_id="{{{{ .parent_id }}}}" """
)

view_issue_tool = JiraPythonTool(
    name="issue_view",
    description="View details of a Jira issue",
    content="""python /tmp/view_issue.py "{{ .issue_key }}" """,
    args=[
        Arg(name="issue_key", default="", type="str", description=f"Issue id, like: JRA-817", required=True)
    ],
    with_files=[
        FileSpec(
            destination="/tmp/view_issue.py",
            content=inspect.getsource(view_issue),
        ),
        FileSpec(
            destination="/tmp/basic_funcs.py",
            content=inspect.getsource(basic_funcs),
        )
    ])

list_issue_tool = JiraPythonTool(
    name="issue_list",
    description="List Jira issues",
    content="""python /tmp/list_issues.py "{{ .project_key }}" "{{ .issues_number }}" """,
    args=[
        Arg(name="project_key", type="str", description="Jira project key", required=True),
        Arg(name="issues_number", type="str", description="Number of issue to list", required=False),
    ],
    with_files=[
        FileSpec(
            destination="/tmp/list_issues.py",
            content=inspect.getsource(list_issues),
        ),
        FileSpec(
            destination="/tmp/basic_funcs.py",
            content=inspect.getsource(basic_funcs),
        )
    ])

add_comment_issue_tool = JiraPythonTool(
    name="issue_add_comment",
    description="Add a comment to a Jira issue",
    content="""python /tmp/create_issue_comment.py "{{ .issue_key }}" "{{ .comment }}" """,
    args=[
        Arg(name="issue_key", type="str", description="Issue key (e.g., 'PROJ-123')", required=True),
        Arg(name="comment", type="str", description="Comment body", required=True),
    ],
    with_files=[
        FileSpec(
            destination="/tmp/create_issue_comment.py",
            content=inspect.getsource(create_issue_comment),
        ),
        FileSpec(
            destination="/tmp/basic_funcs.py",
            content=inspect.getsource(basic_funcs),
        )
    ])

update_issue_status_tool = JiraPythonTool(
    name="update_issue_status",
    description="Update the status of a Jira issue",
    content="""python /tmp/update_issue_status.py "{{ .issue_key }}" "{{ .status }}" """,
    args=[
        Arg(name="issue_key", type="str", description="Issue key (e.g., 'PROJ-123')", required=True),
        Arg(name="status", type="str", description="New status (e.g., 'In Progress', 'Done')", required=True),
    ],
    with_files=[
        FileSpec(
            destination="/tmp/update_issue_status.py",
            content=inspect.getsource(update_issue_status),
        ),
        FileSpec(
            destination="/tmp/basic_funcs.py",
            content=inspect.getsource(basic_funcs),
        )
    ])

assign_issue_tool = JiraPythonTool(
    name="assign_issue",
    description="Assign or unassign a Jira issue",
    content="""python /tmp/assign_issue.py "{{ .issue_key }}" "{{ .assignee_email }}" """,
    args=[
        Arg(name="issue_key", type="str", description="Issue key (e.g., 'PROJ-123')", required=True),
        Arg(name="assignee_email", type="str", description="Email of user to assign (leave empty to unassign)", required=False),
    ],
    with_files=[
        FileSpec(
            destination="/tmp/assign_issue.py",
            content=inspect.getsource(assign_issue),
        ),
        FileSpec(
            destination="/tmp/basic_funcs.py",
            content=inspect.getsource(basic_funcs),
        )
    ])

create_sprint_tool = JiraPythonTool(
    name="create_sprint",
    description="Create a new sprint",
    content="""python /tmp/sprint_ops.py create "{{ .board_id }}" "{{ .name }}" --goal="{{ .goal }}" --start-date="{{ .start_date }}" --end-date="{{ .end_date }}" """,
    args=[
        Arg(name="board_id", type="int", description="Board ID", required=True),
        Arg(name="name", type="str", description="Sprint name", required=True),
        Arg(name="goal", type="str", description="Sprint goal", required=False),
        Arg(name="start_date", type="str", description="Sprint start date (YYYY-MM-DD)", required=False),
        Arg(name="end_date", type="str", description="Sprint end date (YYYY-MM-DD)", required=False),
    ],
    with_files=[
        FileSpec(
            destination="/tmp/sprint_ops.py",
            content=inspect.getsource(sprint_ops),
        ),
        FileSpec(
            destination="/tmp/basic_funcs.py",
            content=inspect.getsource(basic_funcs),
        )
    ])

update_sprint_state_tool = JiraPythonTool(
    name="update_sprint_state",
    description="Start or close a sprint",
    content="""python /tmp/sprint_ops.py state "{{ .sprint_id }}" "{{ .state }}" """,
    args=[
        Arg(name="sprint_id", type="int", description="Sprint ID", required=True),
        Arg(name="state", type="str", description="New state (active/closed)", required=True),
    ],
    with_files=[
        FileSpec(
            destination="/tmp/sprint_ops.py",
            content=inspect.getsource(sprint_ops),
        ),
        FileSpec(
            destination="/tmp/basic_funcs.py",
            content=inspect.getsource(basic_funcs),
        )
    ])

move_to_sprint_tool = JiraPythonTool(
    name="move_to_sprint",
    description="Move issues to a sprint",
    content="""python /tmp/sprint_ops.py move "{{ .sprint_id }}" {{ .issue_keys }} """,
    args=[
        Arg(name="sprint_id", type="int", description="Sprint ID", required=True),
        Arg(name="issue_keys", type="str", description="Space-separated list of issue keys", required=True),
    ],
    with_files=[
        FileSpec(
            destination="/tmp/sprint_ops.py",
            content=inspect.getsource(sprint_ops),
        ),
        FileSpec(
            destination="/tmp/basic_funcs.py",
            content=inspect.getsource(basic_funcs),
        )
    ])

view_sprint_tool = JiraPythonTool(
    name="view_sprint",
    description="View sprint details and issues",
    content="""python /tmp/sprint_ops.py list "{{ .sprint_id }}" """,
    args=[
        Arg(name="sprint_id", type="int", description="Sprint ID", required=True),
    ],
    with_files=[
        FileSpec(
            destination="/tmp/sprint_ops.py",
            content=inspect.getsource(sprint_ops),
        ),
        FileSpec(
            destination="/tmp/basic_funcs.py",
            content=inspect.getsource(basic_funcs),
        )
    ])

[
    register_jira_tool(tool) for tool in [
        create_task_tool,
        create_subtask_tool,
        create_bug_tool,
        create_epic_tool,
        create_story_tool,
        view_issue_tool,
        list_issue_tool,
        add_comment_issue_tool,
        update_issue_status_tool,
        assign_issue_tool,
        create_sprint_tool,
        update_sprint_state_tool,
        move_to_sprint_tool,
        view_sprint_tool,
    ]
]
