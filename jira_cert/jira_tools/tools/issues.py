import inspect
from typing import List
from kubiya_sdk.tools import Arg, FileSpec
from ..base import JiraCertTool, register_jira_tool
from . import create_issue, basic_funcs, view_issue, list_issues, create_issue_comment, update_issue_status, assign_issue, sprint_ops, list_projects, create_release_tasks

class BaseCreationIssueTool(JiraCertTool):
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
            Arg(name="assignee_email", type="str", description=f"Email of user to assign the {issue_type} to (defaults to you if not specified)", required=False),
            Arg(name="label", default="", type="str", description=f"{issue_type} label", required=False),
        ]
        args.extend(extra_args)
        
        tool_files = [
            FileSpec(
                destination="/tmp/create_issue.py",
                content=inspect.getsource(create_issue),
            ),
            FileSpec(
                destination="/tmp/basic_funcs.py",
                content=inspect.getsource(basic_funcs),
            )
        ]

        super().__init__(
            name=name,
            description=description,
            content=content,
            args=args,
            with_files=tool_files)


create_task_tool = BaseCreationIssueTool(name="create_task", issue_type="Task")
create_subtask_tool = BaseCreationIssueTool(
    name="create_subtask",
    issue_type="Sub-task",
    extra_content='--parent_id="{{ .parent_id }}"',
    extra_args=[Arg(name="parent_id", type="str", description="Parent issue key", required=True)],
)
create_bug_tool = BaseCreationIssueTool(name="create_bug", issue_type="Bug")
create_epic_tool = BaseCreationIssueTool(name="create_epic", issue_type="Epic")
create_story_tool = BaseCreationIssueTool(name="create_story", issue_type="Story")

view_issue_tool = JiraCertTool(
    name="view_issue",
    description="View issue details",
    content="""python /tmp/view_issue.py "{{ .issue_key }}" """,
    args=[
        Arg(name="issue_key", type="str", description="Issue key", required=True),
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

list_issue_tool = JiraCertTool(
    name="list_issues",
    description="List issues in project",
    content="""python /tmp/list_issues.py "{{ .project_key }}" "{{ .issues_number }}" "{{ .status }}" "{{ .assignee }}" "{{ .priority }}" "{{ .reporter }}" "{{ .label }}" """,
    args=[
        Arg(name="project_key", type="str", description="Project key", required=True),
        Arg(name="issues_number", type="str", description="Number of issues to list", required=False),
        Arg(name="status", type="str", description="Filter by status", required=False),
        Arg(name="assignee", type="str", description="Filter by assignee", required=False),
        Arg(name="priority", type="str", description="Filter by priority", required=False),
        Arg(name="reporter", type="str", description="Filter by reporter", required=False),
        Arg(name="label", type="str", description="Filter by label", required=False),
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

add_comment_issue_tool = JiraCertTool(
    name="add_comment",
    description="Add comment to issue",
    content="""python /tmp/create_issue_comment.py "{{ .issue_key }}" "{{ .comment }}" """,
    args=[
        Arg(name="issue_key", type="str", description="Issue key", required=True),
        Arg(name="comment", type="str", description="Comment text", required=True),
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

update_issue_status_tool = JiraCertTool(
    name="update_status",
    description="Update issue status",
    content="""python /tmp/update_issue_status.py "{{ .issue_key }}" "{{ .status }}" """,
    args=[
        Arg(name="issue_key", type="str", description="Issue key", required=True),
        Arg(name="status", type="str", description="New status", required=True),
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

assign_issue_tool = JiraCertTool(
    name="assign_issue",
    description="Assign issue to user",
    content="""python /tmp/assign_issue.py "{{ .issue_key }}" "{{ .assignee_email }}" """,
    args=[
        Arg(name="issue_key", type="str", description="Issue key", required=True),
        Arg(name="assignee_email", type="str", description="Email of user to assign (leave empty to unassign)", required=True),
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

# Sprint tools
create_sprint_tool = JiraCertTool(
    name="create_sprint",
    description="Create a new sprint",
    content="""python /tmp/sprint_ops.py create {{ .board_id }} "{{ .name }}" --goal="{{ .goal }}" --start-date="{{ .start_date }}" --end-date="{{ .end_date }}" """,
    args=[
        Arg(name="board_id", type="int", description="Board ID", required=True),
        Arg(name="name", type="str", description="Sprint name", required=True),
        Arg(name="goal", type="str", description="Sprint goal", required=False),
        Arg(name="start_date", type="str", description="Start date (YYYY-MM-DD)", required=False),
        Arg(name="end_date", type="str", description="End date (YYYY-MM-DD)", required=False),
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

update_sprint_state_tool = JiraCertTool(
    name="update_sprint_state",
    description="Update sprint state",
    content="""python /tmp/sprint_ops.py state {{ .sprint_id }} {{ .state }}""",
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

move_to_sprint_tool = JiraCertTool(
    name="move_to_sprint",
    description="Move issues to sprint",
    content="""python /tmp/sprint_ops.py move {{ .sprint_id }} {{ .issue_keys }}""",
    args=[
        Arg(name="sprint_id", type="int", description="Sprint ID", required=True),
        Arg(name="issue_keys", type="str", description="Space-separated issue keys", required=True),
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

view_sprint_tool = JiraCertTool(
    name="view_sprint",
    description="View sprint details and issues",
    content="""python /tmp/sprint_ops.py list {{ .sprint_id }}""",
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

list_projects_tool = JiraCertTool(
    name="list_projects",
    description="List all accessible Jira projects",
    content="python /tmp/list_projects.py",
    args=[],
    with_files=[
        FileSpec(
            destination="/tmp/list_projects.py",
            content=inspect.getsource(list_projects),
        ),
        FileSpec(
            destination="/tmp/basic_funcs.py",
            content=inspect.getsource(basic_funcs),
        )
    ])

create_release_tasks_tool = JiraCertTool(
    name="create_release_tasks",
    description="Create a release task with 7 subtasks for different environments in KUBIKA2 board",
    content="""python /tmp/create_release_tasks.py "{{ .release_date }}" """,
    args=[
        Arg(name="release_date", type="str", description="Release date in DD.MM.YY format (e.g., 25.05.24)", required=True),
    ],
    with_files=[
        FileSpec(
            destination="/tmp/create_release_tasks.py",
            content=inspect.getsource(create_release_tasks),
        ),
        FileSpec(
            destination="/tmp/create_issue.py",
            content=inspect.getsource(create_issue),
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
        list_projects_tool,
        create_release_tasks_tool
    ]
] 