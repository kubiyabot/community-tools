from kubiya_sdk.tools import Arg
from .base import ArgoCDTool
from kubiya_sdk.tools.registry import tool_registry

argocd_login = ArgoCDTool(
    name="argocd_login",
    description="Login to ArgoCD server",
    content="""
    argocd login $ARGOCD_SERVER_URL --auth-token $ARGOCD_TOKEN --insecure
    """,
    args=[],
)

argocd_list_applications = ArgoCDTool(
    name="argocd_list_applications",
    description="List ArgoCD applications with detailed output",
    content="""
    argocd app list -o wide
    """,
    args=[],
)

argocd_get_application = ArgoCDTool(
    name="argocd_get_application",
    description="Get detailed information of an ArgoCD application",
    content="""
    argocd app get $app_name --output json
    """,
    args=[
        Arg(name="app_name", type="str", description="Name of the ArgoCD application", required=True),
    ],
)

argocd_sync_application = ArgoCDTool(
    name="argocd_sync_application",
    description="Sync an ArgoCD application with advanced options",
    content="""
    argocd app sync $app_name --prune --force --timeout $timeout --retry-limit $retry_limit
    """,
    args=[
        Arg(name="app_name", type="str", description="Name of the ArgoCD application to sync", required=True),
        Arg(name="timeout", type="int", description="Timeout (in seconds) for the sync operation", default=300),
        Arg(name="retry_limit", type="int", description="Number of sync retries", default=5),
    ],
)

argocd_create_application = ArgoCDTool(
    name="argocd_create_application",
    description="Create a new ArgoCD application with advanced configuration",
    content="""
    argocd app create $app_name --repo $repo_url --path $repo_path --dest-server $dest_server --dest-namespace $dest_namespace --revision $revision --sync-policy $sync_policy --auto-prune --self-heal
    """,
    args=[
        Arg(name="app_name", type="str", description="Name of the new ArgoCD application", required=True),
        Arg(name="repo_url", type="str", description="URL of the Git repository", required=True),
        Arg(name="repo_path", type="str", description="Path within the Git repository", required=True),
        Arg(name="dest_server", type="str", description="Destination server URL", required=True),
        Arg(name="dest_namespace", type="str", description="Destination namespace", required=True),
        Arg(name="revision", type="str", description="Revision to use (branch, tag, or commit SHA)", default="HEAD"),
        Arg(name="sync_policy", type="str", description="Sync policy (manual, automated)", default="manual"),
    ],
)

argocd_delete_application = ArgoCDTool(
    name="argocd_delete_application",
    description="Delete an ArgoCD application with advanced options",
    content="""
    argocd app delete $app_name --cascade --propagation-policy $propagation_policy --force
    """,
    args=[
        Arg(name="app_name", type="str", description="Name of the ArgoCD application to delete", required=True),
        Arg(name="propagation_policy", type="str", description="Propagation policy for deletion", default="foreground"),
    ],
)

argocd_rollback_application = ArgoCDTool(
    name="argocd_rollback_application",
    description="Rollback an ArgoCD application to a previous version",
    content="""
    argocd app rollback $app_name $revision --prune
    """,
    args=[
        Arg(name="app_name", type="str", description="Name of the ArgoCD application to rollback", required=True),
        Arg(name="revision", type="str", description="Revision to rollback to", required=True),
    ],
)

argocd_set_app_parameters = ArgoCDTool(
    name="argocd_set_app_parameters",
    description="Set parameters for an ArgoCD application",
    content="""
    argocd app set $app_name -p $parameters
    """,
    args=[
        Arg(name="app_name", type="str", description="Name of the ArgoCD application", required=True),
        Arg(name="parameters", type="str", description="Comma-separated list of parameter key-value pairs", required=True),
    ],
)

argocd_get_project = ArgoCDTool(
    name="argocd_get_project",
    description="Get detailed information of an ArgoCD project",
    content="""
    argocd proj get $project_name -o json
    """,
    args=[
        Arg(name="project_name", type="str", description="Name of the ArgoCD project", required=True),
    ],
)

argocd_create_project = ArgoCDTool(
    name="argocd_create_project",
    description="Create a new ArgoCD project with advanced configuration",
    content="""
    argocd proj create $project_name --description "$description" --allow-cluster-resource $cluster_resources --source-repo $source_repos --destination $destinations
    """,
    args=[
        Arg(name="project_name", type="str", description="Name of the new ArgoCD project", required=True),
        Arg(name="description", type="str", description="Project description", default=""),
        Arg(name="cluster_resources", type="str", description="Allowed cluster-scoped resources", default=""),
        Arg(name="source_repos", type="str", description="Allowed source repositories (comma-separated)", default=""),
        Arg(name="destinations", type="str", description="Allowed destination servers/namespaces (comma-separated)", default=""),
    ],
)

argocd_delete_project = ArgoCDTool(
    name="argocd_delete_project",
    description="Delete an ArgoCD project",
    content="""
    argocd proj delete $project_name
    """,
    args=[
        Arg(name="project_name", type="str", description="Name of the ArgoCD project to delete", required=True),
    ],
)

argocd_list_repositories = ArgoCDTool(
    name="argocd_list_repositories",
    description="List configured Git repositories in ArgoCD",
    content="""
    argocd repo list -o wide
    """,
    args=[],
)

argocd_add_repository = ArgoCDTool(
    name="argocd_add_repository",
    description="Add a new Git repository to ArgoCD",
    content="""
    argocd repo add $repo_url --name $repo_name --username $username --password $password --insecure-skip-server-verification
    """,
    args=[
        Arg(name="repo_url", type="str", description="URL of the Git repository", required=True),
        Arg(name="repo_name", type="str", description="Name for the repository", required=True),
        Arg(name="username", type="str", description="Username for repository authentication", default=""),
        Arg(name="password", type="str", description="Password for repository authentication", default=""),
    ],
)

# Register all ArgoCD tools
for tool in [argocd_login, argocd_list_applications, argocd_get_application, argocd_sync_application,
             argocd_create_application, argocd_delete_application, argocd_rollback_application,
             argocd_set_app_parameters, argocd_get_project, argocd_create_project, argocd_delete_project,
             argocd_list_repositories, argocd_add_repository]:
    tool_registry.register("argocd", tool)