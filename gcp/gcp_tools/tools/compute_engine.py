from kubiya_sdk.tools import Arg
from .base import GCPTool, register_gcp_tool

gce_list_instances = GCPTool(
    name="gce_list_instances",
    description="List Compute Engine instances",
    content="gcloud compute instances list --format=json",
    args=[],
    mermaid_diagram="..."  # Add mermaid diagram here
)

gce_start_instance = GCPTool(
    name="gce_start_instance",
    description="Start a Compute Engine instance",
    content="gcloud compute instances start $instance_name --zone=$zone",
    args=[
        Arg(name="instance_name", type="str", description="Name of the instance to start", required=True),
        Arg(name="zone", type="str", description="Zone of the instance", required=True),
    ],
    mermaid_diagram="..."  # Add mermaid diagram here
)

gce_stop_instance = GCPTool(
    name="gce_stop_instance",
    description="Stop a Compute Engine instance",
    content="gcloud compute instances stop $instance_name --zone=$zone",
    args=[
        Arg(name="instance_name", type="str", description="Name of the instance to stop", required=True),
        Arg(name="zone", type="str", description="Zone of the instance", required=True),
    ],
    mermaid_diagram="..."  # Add mermaid diagram here
)

gce_create_instance = GCPTool(
    name="gce_create_instance",
    description="Create a new Compute Engine instance",
    content="gcloud compute instances create $instance_name --zone=$zone --machine-type=$machine_type --image-family=$image_family --image-project=$image_project",
    args=[
        Arg(name="instance_name", type="str", description="Name of the new instance", required=True),
        Arg(name="zone", type="str", description="Zone for the new instance", required=True),
        Arg(name="machine_type", type="str", description="Machine type for the new instance", required=True),
        Arg(name="image_family", type="str", description="Image family for the new instance", required=True),
        Arg(name="image_project", type="str", description="Image project for the new instance", required=True),
    ],
    mermaid_diagram="..."  # Add mermaid diagram here
)

for tool in [gce_list_instances, gce_start_instance, gce_stop_instance, gce_create_instance]:
    register_gcp_tool(tool)