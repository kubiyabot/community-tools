from kubiya_sdk.tools import Arg
from .base import GCPTool, register_gcp_tool

sql_list_instances = GCPTool(
    name="sql_list_instances",
    description="List Cloud SQL instances",
    content="gcloud sql instances list --format=json",
    args=[],
    mermaid_diagram="..."  # Add mermaid diagram here
)

sql_create_instance = GCPTool(
    name="sql_create_instance",
    description="Create a new Cloud SQL instance",
    content="gcloud sql instances create $instance_name --database-version=$database_version --tier=$tier --region=$region",
    args=[
        Arg(name="instance_name", type="str", description="Name of the new instance", required=True),
        Arg(name="database_version", type="str", description="Database version (e.g., MYSQL_5_7)", required=True),
        Arg(name="tier", type="str", description="Machine tier (e.g., db-n1-standard-1)", required=True),
        Arg(name="region", type="str", description="Region for the new instance", required=True),
    ],
    mermaid_diagram="..."  # Add mermaid diagram here
)

for tool in [sql_list_instances, sql_create_instance]:
    register_gcp_tool(tool)