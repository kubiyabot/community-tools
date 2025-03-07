from kubiya_sdk.tools import Arg
from .base import GCPTool, register_gcp_tool

gcs_list_buckets = GCPTool(
    name="gcs_list_buckets",
    description="List Cloud Storage buckets",
    content="gsutil ls",
    args=[],
    mermaid_diagram="..."  # Add mermaid diagram here
)

gcs_create_bucket = GCPTool(
    name="gcs_create_bucket",
    description="Create a new Cloud Storage bucket",
    content="gsutil mb -l $location gs://$bucket_name",
    args=[
        Arg(name="bucket_name", type="str", description="Name of the new bucket", required=True),
        Arg(name="location", type="str", description="Location for the new bucket", required=True),
    ],
    mermaid_diagram="..."  # Add mermaid diagram here
)

gcs_upload_file = GCPTool(
    name="gcs_upload_file",
    description="Upload a file to a Cloud Storage bucket",
    content="gsutil cp $local_file gs://$bucket_name/$remote_path",
    args=[
        Arg(name="local_file", type="str", description="Path to the local file", required=True),
        Arg(name="bucket_name", type="str", description="Name of the bucket", required=True),
        Arg(name="remote_path", type="str", description="Remote path in the bucket", required=True),
    ],
    mermaid_diagram="..."  # Add mermaid diagram here
)

for tool in [gcs_list_buckets, gcs_create_bucket, gcs_upload_file]:
    register_gcp_tool(tool)