from kubiya_sdk.tools import Arg
from .base import GitHubCliTool
from kubiya_sdk.tools.registry import tool_registry

workflow_list = GitHubCliTool(
    name="github_workflow_list",
    description="List GitHub Actions workflows in a repository.",
    content="gh workflow list --repo $repo $([[ -n \"$limit\" ]] && echo \"--limit $limit\")",
    args=[
        Arg(name="repo", type="str", description="Repository name in 'owner/repo' format. Example: 'octocat/Hello-World'", required=True),
        Arg(name="limit", type="int", description="Maximum number of workflows to list. Example: 10", required=False),
    ],
)

workflow_view = GitHubCliTool(
    name="github_workflow_view",
    description="View details of a specific GitHub Actions workflow.",
    content="gh workflow view --repo $repo $workflow",
    args=[
        Arg(name="repo", type="str", description="Repository name in 'owner/repo' format. Example: 'octocat/Hello-World'", required=True),
        Arg(name="workflow", type="str", description="Workflow name or ID. Example: 'main.yml' or '1234567'", required=True),
    ],
)

workflow_run = GitHubCliTool(
    name="github_workflow_run",
    description="Manually trigger a GitHub Actions workflow.",
    content="gh workflow run --repo $repo $workflow $([[ -n \"$ref\" ]] && echo \"--ref $ref\") $([[ -n \"$inputs\" ]] && echo \"--raw-field $inputs\")",
    args=[
        Arg(name="repo", type="str", description="Repository name in 'owner/repo' format. Example: 'octocat/Hello-World'", required=True),
        Arg(name="workflow", type="str", description="Workflow name or ID. Example: 'main.yml' or '1234567'", required=True),
        Arg(name="ref", type="str", description="Branch or tag name to run workflow on. Example: 'main'", required=False),
        Arg(name="inputs", type="str", description="JSON object of input keys and values. Example: '{\"name\":\"value\"}'", required=False),
    ],
)

workflow_disable = GitHubCliTool(
    name="github_workflow_disable",
    description="Disable a GitHub Actions workflow.",
    content="gh workflow disable --repo $repo $workflow",
    args=[
        Arg(name="repo", type="str", description="Repository name in 'owner/repo' format. Example: 'octocat/Hello-World'", required=True),
        Arg(name="workflow", type="str", description="Workflow name or ID. Example: 'main.yml' or '1234567'", required=True),
    ],
)

workflow_enable = GitHubCliTool(
    name="github_workflow_enable",
    description="Enable a GitHub Actions workflow.",
    content="gh workflow enable --repo $repo $workflow",
    args=[
        Arg(name="repo", type="str", description="Repository name in 'owner/repo' format. Example: 'octocat/Hello-World'", required=True),
        Arg(name="workflow", type="str", description="Workflow name or ID. Example: 'main.yml' or '1234567'", required=True),
    ],
)

workflow_create = GitHubCliTool(
    name="github_workflow_create",
    description="Create a new GitHub Actions workflow.",
    content="""
    mkdir -p .github/workflows
    echo "$content" > .github/workflows/$name
    gh workflow enable --repo $repo .github/workflows/$name
    """,
    args=[
        Arg(name="repo", type="str", description="Repository name in 'owner/repo' format. Example: 'octocat/Hello-World'", required=True),
        Arg(name="name", type="str", description="Name of the workflow file. Example: 'main.yml'", required=True),
        Arg(name="content", type="str", description="YAML content of the workflow. Example: 'name: CI\non: [push]\njobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v2\n      - run: npm test'", required=True),
    ],
)

workflow_delete = GitHubCliTool(
    name="github_workflow_delete",
    description="Delete a GitHub Actions workflow.",
    content="gh api --method DELETE /repos/$repo/actions/workflows/$workflow",
    args=[
        Arg(name="repo", type="str", description="Repository name in 'owner/repo' format. Example: 'octocat/Hello-World'", required=True),
        Arg(name="workflow", type="str", description="Workflow ID. Example: '1234567'", required=True),
    ],
)

workflow_run_list = GitHubCliTool(
    name="github_workflow_run_list",
    description="List recent runs of a GitHub Actions workflow.",
    content="gh run list --repo $repo --workflow $workflow $([[ -n \"$limit\" ]] && echo \"--limit $limit\")",
    args=[
        Arg(name="repo", type="str", description="Repository name in 'owner/repo' format. Example: 'octocat/Hello-World'", required=True),
        Arg(name="workflow", type="str", description="Workflow name or ID. Example: 'main.yml' or '1234567'", required=True),
        Arg(name="limit", type="int", description="Maximum number of runs to list. Example: 10", required=False),
    ],
)

workflow_run_view = GitHubCliTool(
    name="github_workflow_run_view",
    description="View details of a specific workflow run.",
    content="gh run view --repo $repo $run_id",
    args=[
        Arg(name="repo", type="str", description="Repository name in 'owner/repo' format. Example: 'octocat/Hello-World'", required=True),
        Arg(name="run_id", type="str", description="Run ID. Example: '1234567890'", required=True),
    ],
)

workflow_run_logs = GitHubCliTool(
    name="github_workflow_run_logs",
    description="View logs of a specific workflow run.",
    content="gh run view --repo $repo $run_id --log",
    args=[
        Arg(name="repo", type="str", description="Repository name in 'owner/repo' format. Example: 'octocat/Hello-World'", required=True),
        Arg(name="run_id", type="str", description="Run ID. Example: '1234567890'", required=True),
    ],
)

workflow_run_logs_failed = GitHubCliTool(
    name="workflow_run_logs_failed",
    description="View failure logs only of a specific workflow run.",
    content="gh run view --repo $repo $run_id --log-failed",
    args=[
        Arg(name="repo", type="str", description="Repository name in 'owner/repo' format. Example: 'octocat/Hello-World'", required=True),
        Arg(name="run_id", type="str", description="Run ID. Example: '1234567890'", required=True),
    ],
)

workflow_run_cancel = GitHubCliTool(
    name="github_workflow_run_cancel",
    description="Cancel a workflow run.",
    content="gh run cancel --repo $repo $run_id",
    args=[
        Arg(name="repo", type="str", description="Repository name in 'owner/repo' format. Example: 'octocat/Hello-World'", required=True),
        Arg(name="run_id", type="str", description="Run ID. Example: '1234567890'", required=True),
    ],
)

workflow_run_rerun = GitHubCliTool(
    name="github_workflow_run_rerun",
    description="Rerun a workflow run.",
    content="gh run rerun --repo $repo $run_id",
    args=[
        Arg(name="repo", type="str", description="Repository name in 'owner/repo' format. Example: 'octocat/Hello-World'", required=True),
        Arg(name="run_id", type="str", description="Run ID. Example: '1234567890'", required=True),
    ],
)

workflow_clone_repo = GitHubCliTool(
    name="github_workflow_clone_repo",
    description="Clone a repository containing GitHub Actions workflows.",
    content="""
    gh repo clone $repo $([[ -n "$directory" ]] && echo "$directory")
    cd $([[ -n "$directory" ]] && echo "$directory" || echo "$(basename $repo)")
    echo "Repository cloned successfully."
    """,
    args=[
        Arg(name="repo", type="str", description="Repository name in 'owner/repo' format. Example: 'octocat/Hello-World'", required=True),
        Arg(name="directory", type="str", description="Directory to clone into. If not specified, uses the repository name.", required=False),
    ],
)

workflow_discover_files = GitHubCliTool(
    name="github_workflow_discover_files",
    description="Discover GitHub Actions workflow files in a repository.",
    content="""
    gh repo clone $repo temp_repo
    cd temp_repo
    echo "Workflow files found:"
    find .github/workflows -name "*.yml" -o -name "*.yaml"
    cd ..
    rm -rf temp_repo
    """,
    args=[
        Arg(name="repo", type="str", description="Repository name in 'owner/repo' format. Example: 'octocat/Hello-World'", required=True),
    ],
)

workflow_lint = GitHubCliTool(
    name="github_workflow_lint",
    description="Lint a GitHub Actions workflow file.",
    content="""
    gh workflow lint $file_path
    """,
    args=[
        Arg(name="file_path", type="str", description="Path to the workflow file. Example: '.github/workflows/ci.yml'", required=True),
    ],
)

workflow_visualize = GitHubCliTool(
    name="github_workflow_visualize",
    description="Visualize a GitHub Actions workflow (outputs a URL to view the workflow).",
    content="""
    echo "https://github.com/$repo/actions/workflows/$(basename $workflow_file)"
    """,
    args=[
        Arg(name="repo", type="str", description="Repository name in 'owner/repo' format. Example: 'octocat/Hello-World'", required=True),
        Arg(name="workflow_file", type="str", description="Name of the workflow file. Example: 'ci.yml'", required=True),
    ],
)

workflow_dispatch_event = GitHubCliTool(
    name="github_workflow_dispatch_event",
    description="Manually trigger a workflow using the 'workflow_dispatch' event.",
    content="""
    gh workflow run $workflow_file --repo $repo $([[ -n "$ref" ]] && echo "--ref $ref") $([[ -n "$inputs" ]] && echo "--raw-field $inputs")
    """,
    args=[
        Arg(name="repo", type="str", description="Repository name in 'owner/repo' format. Example: 'octocat/Hello-World'", required=True),
        Arg(name="workflow_file", type="str", description="Name or ID of the workflow file. Example: 'ci.yml' or '1234567'", required=True),
        Arg(name="ref", type="str", description="The branch or tag name to run the workflow on. Example: 'main'", required=False),
        Arg(name="inputs", type="str", description="JSON object of input keys and values. Example: '{\"name\":\"value\"}'", required=False),
    ],
)

workflow_get_usage = GitHubCliTool(
    name="github_workflow_get_usage",
    description="Get the usage of GitHub Actions in a repository.",
    content="""
    gh api repos/$repo/actions/workflows | jq '.workflows[] | {name: .name, state: .state, path: .path}'
    """,
    args=[
        Arg(name="repo", type="str", description="Repository name in 'owner/repo' format. Example: 'octocat/Hello-World'", required=True),
    ],
)

workflow_set_secret = GitHubCliTool(
    name="github_workflow_set_secret",
    description="Set a secret for GitHub Actions in a repository.",
    content="""
    gh secret set $secret_name --body "$secret_value" --repo $repo
    """,
    args=[
        Arg(name="repo", type="str", description="Repository name in 'owner/repo' format. Example: 'octocat/Hello-World'", required=True),
        Arg(name="secret_name", type="str", description="Name of the secret. Example: 'API_KEY'", required=True),
        Arg(name="secret_value", type="str", description="Value of the secret. Example: 'abcdef123456'", required=True),
    ],
)

# Register all workflow tools
for tool in [
    workflow_list, workflow_view, workflow_run, workflow_disable, workflow_enable,
    workflow_create, workflow_delete, workflow_run_list, workflow_run_view,
    workflow_run_logs,workflow_run_logs_failed, workflow_run_cancel, workflow_run_rerun,
    workflow_clone_repo, workflow_discover_files, workflow_lint,
    workflow_visualize, workflow_dispatch_event, workflow_get_usage,
    workflow_set_secret
]:
    tool_registry.register("github", tool)

__all__ = [
    'workflow_list', 'workflow_view', 'workflow_run', 'workflow_disable', 'workflow_enable',
    'workflow_create', 'workflow_delete', 'workflow_run_list', 'workflow_run_view',
    'workflow_run_logs','workflow_run_logs_failed', 'workflow_run_cancel', 'workflow_run_rerun',
    'workflow_clone_repo', 'workflow_discover_files', 'workflow_lint',
    'workflow_visualize', 'workflow_dispatch_event', 'workflow_get_usage',
    'workflow_set_secret'
]