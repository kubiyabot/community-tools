import inspect

from kubiya_sdk.tools import Arg, FileSpec

from ..base import JiraPythonTool, register_jira_tool
from . import create_issue, basic_funcs

create_issue_tool = JiraPythonTool(
    name="create_issue",
    description="Create new jira issue",
    content="""
    pip install requests > /dev/null 2>&1
    pip install kubiya-sdk > /dev/null 2>&1
    python /tmp/create_issue.py "{{ .project_key }}" "{{ .name }}" "{{ .description }}" "{{ .issue_type }}" "{{ .priority }}" "{{ .assignee_email }}"
    """,

    args=[
        Arg(name="project_key", type="str", description="Jira project key", required=True),
        Arg(name="name", type="str", description="Issue name", required=True),
        Arg(name="issue_type", type="str", description="Issue type, such as Task, Sub-Task, Epic, Bug etc.",
            required=True),
        Arg(name="description", type="str", description="Issue description", required=True),
        Arg(name="priority", type="str", description="Issue priority can be Low Medium or High", required=False),
        Arg(name="assignee_email", type="str", description="Issue assignee user", required=False),
        # Arg(name="labels", type="array", description="Issue labels", required=False),
    ],
    with_files=[
        FileSpec(
            destination="/tmp/create_issue.py",
            content=inspect.getsource(create_issue),
        ),
        FileSpec(
            destination="/tmp/basic_funcs.py",
            content=inspect.getsource(basic_funcs),
        ),
        # FileSpec(
        #     destination="/tmp/requirements.txt",
        #     # content=basic_funcs.get_file_content("requirements.txt"),
        #     context="kubiya-sdk\nrequests"
        # )
    ]

)

register_jira_tool(create_issue_tool)
