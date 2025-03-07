from kubiya_sdk.tools import Arg
from .base import GCPTool, register_gcp_tool

gke_list_clusters = GCPTool(
    name="gke_list_clusters",
    description="List GKE clusters",
    content="gcloud container clusters list --format=json",
    args=[],
    mermaid_diagram="..."  # Add mermaid diagram here
)

gke_create_cluster = GCPTool(
    name="gke_create_cluster",
    description="Create a new GKE cluster",
    content="gcloud container clusters create $cluster_name --num-nodes=$num_nodes --zone=$zone",
    args=[
        Arg(name="cluster_name", type="str", description="Name of the new cluster", required=True),
        Arg(name="num_nodes", type="int", description="Number of nodes in the cluster", required=True),
        Arg(name="zone", type="str", description="Zone for the new cluster", required=True),
    ],
    mermaid_diagram="..."  # Add mermaid diagram here
)

for tool in [gke_list_clusters, gke_create_cluster]:
    register_gcp_tool(tool)