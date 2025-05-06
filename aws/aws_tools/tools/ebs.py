from kubiya_sdk.tools import Arg
from .base import AWSCliTool, AWSSdkTool
from kubiya_sdk.tools.registry import tool_registry

ebs_create_volume = AWSCliTool(
    name="ebs_create_volume",
    description="Create an EBS volume",
    content="aws ec2 create-volume --availability-zone $availability_zone --size $size --volume-type $volume_type $([[ -n \"$snapshot_id\" ]] && echo \"--snapshot-id $snapshot_id\")",
    args=[
        Arg(name="availability_zone", type="str", description="Availability Zone (e.g., 'us-west-2a')", required=True),
        Arg(name="size", type="int", description="Size in GiB", required=True),
        Arg(name="volume_type", type="str", description="Volume type (e.g., 'gp2', 'io1', 'st1')", required=True),
        Arg(name="snapshot_id", type="str", description="Snapshot ID to create volume from (optional)", required=False),
    ],
    mermaid_diagram="""
    graph TD
        A[👤 User] -->|Request: Create EBS volume| B[🤖 TeamMate]
        B --> C{{"Volume details?" 💾}}
        C --> D[User provides details ✍️]
        D --> E[API request to AWS ☁️]
        E --> F[AWS creates volume 🔧]
        F --> G[User receives volume ID 📄]

        style A fill:#f0f9ff,stroke:#0369a1,stroke-width:2px;
        style B fill:#dbeafe,stroke:#3b82f6,stroke-width:2px;
        style C fill:#d1fae5,stroke:#059669,stroke-width:2px;
        style D fill:#bbf7d0,stroke:#16a34a,stroke-width:2px;
        style E fill:#fee2e2,stroke:#ef4444,stroke-width:2px;
        style F fill:#ffedd5,stroke:#ea580c,stroke-width:2px;
        style G fill:#e0f2fe,stroke:#0284c7,stroke-width:2px;
    """
)

ebs_delete_volume = AWSCliTool(
    name="ebs_delete_volume",
    description="Delete an EBS volume",
    content="aws ec2 delete-volume --volume-id $volume_id",
    args=[
        Arg(name="volume_id", type="str", description="Volume ID to delete (e.g., 'vol-1234567890abcdef0')", required=True),
    ],
    mermaid_diagram="""
    graph TD
        A[👤 User] -->|Request: Delete EBS volume| B[🤖 TeamMate]
        B --> C{{"Volume ID?" 💾}}
        C --> D[User provides volume ID ✍️]
        D --> E[API request to AWS ☁️]
        E --> F[AWS deletes volume 🗑️]
        F --> G[User receives confirmation 📄]

        style A fill:#f0f9ff,stroke:#0369a1,stroke-width:2px;
        style B fill:#dbeafe,stroke:#3b82f6,stroke-width:2px;
        style C fill:#d1fae5,stroke:#059669,stroke-width:2px;
        style D fill:#bbf7d0,stroke:#16a34a,stroke-width:2px;
        style E fill:#fee2e2,stroke:#ef4444,stroke-width:2px;
        style F fill:#ffedd5,stroke:#ea580c,stroke-width:2px;
        style G fill:#e0f2fe,stroke:#0284c7,stroke-width:2px;
    """
)

ebs_attach_volume = AWSCliTool(
    name="ebs_attach_volume",
    description="Attach an EBS volume to an EC2 instance",
    content="aws ec2 attach-volume --volume-id $volume_id --instance-id $instance_id --device $device",
    args=[
        Arg(name="volume_id", type="str", description="Volume ID to attach (e.g., 'vol-1234567890abcdef0')", required=True),
        Arg(name="instance_id", type="str", description="Instance ID to attach to (e.g., 'i-1234567890abcdef0')", required=True),
        Arg(name="device", type="str", description="Device name (e.g., '/dev/sdf')", required=True),
    ],
    mermaid_diagram="""
    graph TD
        A[👤 User] -->|Request: Attach volume| B[🤖 TeamMate]
        B --> C{{"Volume and instance details?" 💾}}
        C --> D[User provides details ✍️]
        D --> E[API request to AWS ☁️]
        E --> F[AWS attaches volume 🔌]
        F --> G[User receives confirmation 📄]

        style A fill:#f0f9ff,stroke:#0369a1,stroke-width:2px;
        style B fill:#dbeafe,stroke:#3b82f6,stroke-width:2px;
        style C fill:#d1fae5,stroke:#059669,stroke-width:2px;
        style D fill:#bbf7d0,stroke:#16a34a,stroke-width:2px;
        style E fill:#fee2e2,stroke:#ef4444,stroke-width:2px;
        style F fill:#ffedd5,stroke:#ea580c,stroke-width:2px;
        style G fill:#e0f2fe,stroke:#0284c7,stroke-width:2px;
    """
)

ebs_detach_volume = AWSCliTool(
    name="ebs_detach_volume",
    description="Detach an EBS volume from an EC2 instance",
    content="aws ec2 detach-volume --volume-id $volume_id",
    args=[
        Arg(name="volume_id", type="str", description="Volume ID to detach (e.g., 'vol-1234567890abcdef0')", required=True),
    ],
    mermaid_diagram="""
    graph TD
        A[👤 User] -->|Request: Detach volume| B[🤖 TeamMate]
        B --> C{{"Volume ID?" 💾}}
        C --> D[User provides volume ID ✍️]
        D --> E[API request to AWS ☁️]
        E --> F[AWS detaches volume 🔌]
        F --> G[User receives confirmation 📄]

        style A fill:#f0f9ff,stroke:#0369a1,stroke-width:2px;
        style B fill:#dbeafe,stroke:#3b82f6,stroke-width:2px;
        style C fill:#d1fae5,stroke:#059669,stroke-width:2px;
        style D fill:#bbf7d0,stroke:#16a34a,stroke-width:2px;
        style E fill:#fee2e2,stroke:#ef4444,stroke-width:2px;
        style F fill:#ffedd5,stroke:#ea580c,stroke-width:2px;
        style G fill:#e0f2fe,stroke:#0284c7,stroke-width:2px;
    """
)

ebs_list_volumes = AWSCliTool(
    name="ebs_list_volumes",
    description="List EBS volumes",
    content="aws ec2 describe-volumes $([[ -n \"$filters\" ]] && echo \"--filters $filters\")",
    args=[
        Arg(name="filters", type="str", description="Filters in JSON format (optional)", required=False),
    ],
    mermaid_diagram="""
    graph TD
        A[👤 User] -->|Request: List volumes| B[🤖 TeamMate]
        B --> C[API request to AWS ☁️]
        C --> D[AWS retrieves volume list 💾]
        D --> E[User receives volume details 📄]

        style A fill:#f0f9ff,stroke:#0369a1,stroke-width:2px;
        style B fill:#dbeafe,stroke:#3b82f6,stroke-width:2px;
        style C fill:#fee2e2,stroke:#ef4444,stroke-width:2px;
        style D fill:#ffedd5,stroke:#ea580c,stroke-width:2px;
        style E fill:#e0f2fe,stroke:#0284c7,stroke-width:2px;
    """
)

ebs_create_snapshot = AWSCliTool(
    name="ebs_create_snapshot",
    description="Create a snapshot of an EBS volume",
    content="aws ec2 create-snapshot --volume-id $volume_id --description \"$description\"",
    args=[
        Arg(name="volume_id", type="str", description="Volume ID to snapshot (e.g., 'vol-1234567890abcdef0')", required=True),
        Arg(name="description", type="str", description="Description for the snapshot", required=True),
    ],
    mermaid_diagram="""
    graph TD
        A[👤 User] -->|Request: Create snapshot| B[🤖 TeamMate]
        B --> C{{"Volume details?" 💾}}
        C --> D[User provides details ✍️]
        D --> E[API request to AWS ☁️]
        E --> F[AWS creates snapshot 📸]
        F --> G[User receives snapshot ID 📄]

        style A fill:#f0f9ff,stroke:#0369a1,stroke-width:2px;
        style B fill:#dbeafe,stroke:#3b82f6,stroke-width:2px;
        style C fill:#d1fae5,stroke:#059669,stroke-width:2px;
        style D fill:#bbf7d0,stroke:#16a34a,stroke-width:2px;
        style E fill:#fee2e2,stroke:#ef4444,stroke-width:2px;
        style F fill:#ffedd5,stroke:#ea580c,stroke-width:2px;
        style G fill:#e0f2fe,stroke:#0284c7,stroke-width:2px;
    """
)

ebs_delete_snapshot = AWSCliTool(
    name="ebs_delete_snapshot",
    description="Delete an EBS snapshot",
    content="aws ec2 delete-snapshot --snapshot-id $snapshot_id",
    args=[
        Arg(name="snapshot_id", type="str", description="Snapshot ID to delete (e.g., 'snap-1234567890abcdef0')", required=True),
    ],
    mermaid_diagram="""
    graph TD
        A[👤 User] -->|Request: Delete snapshot| B[🤖 TeamMate]
        B --> C{{"Snapshot ID?" 📸}}
        C --> D[User provides snapshot ID ✍️]
        D --> E[API request to AWS ☁️]
        E --> F[AWS deletes snapshot 🗑️]
        F --> G[User receives confirmation 📄]

        style A fill:#f0f9ff,stroke:#0369a1,stroke-width:2px;
        style B fill:#dbeafe,stroke:#3b82f6,stroke-width:2px;
        style C fill:#d1fae5,stroke:#059669,stroke-width:2px;
        style D fill:#bbf7d0,stroke:#16a34a,stroke-width:2px;
        style E fill:#fee2e2,stroke:#ef4444,stroke-width:2px;
        style F fill:#ffedd5,stroke:#ea580c,stroke-width:2px;
        style G fill:#e0f2fe,stroke:#0284c7,stroke-width:2px;
    """
)

ebs_list_snapshots = AWSCliTool(
    name="ebs_list_snapshots",
    description="List EBS snapshots",
    content="aws ec2 describe-snapshots --owner-ids self $([[ -n \"$filters\" ]] && echo \"--filters $filters\")",
    args=[
        Arg(name="filters", type="str", description="Filters in JSON format (optional)", required=False),
    ],
    mermaid_diagram="""
    graph TD
        A[👤 User] -->|Request: List snapshots| B[🤖 TeamMate]
        B --> C[API request to AWS ☁️]
        C --> D[AWS retrieves snapshot list 📸]
        D --> E[User receives snapshot details 📄]

        style A fill:#f0f9ff,stroke:#0369a1,stroke-width:2px;
        style B fill:#dbeafe,stroke:#3b82f6,stroke-width:2px;
        style C fill:#fee2e2,stroke:#ef4444,stroke-width:2px;
        style D fill:#ffedd5,stroke:#ea580c,stroke-width:2px;
        style E fill:#e0f2fe,stroke:#0284c7,stroke-width:2px;
    """
)

ebs_copy_snapshot = AWSCliTool(
    name="ebs_copy_snapshot",
    description="Copy an EBS snapshot",
    content="aws ec2 copy-snapshot --source-region $source_region --source-snapshot-id $source_snapshot_id --description \"$description\" --destination-region $destination_region",
    args=[
        Arg(name="source_region", type="str", description="Source region (e.g., 'us-west-2')", required=True),
        Arg(name="source_snapshot_id", type="str", description="Source snapshot ID (e.g., 'snap-1234567890abcdef0')", required=True),
        Arg(name="description", type="str", description="Description for the new snapshot", required=True),
        Arg(name="destination_region", type="str", description="Destination region (e.g., 'us-east-1')", required=True),
    ],
    mermaid_diagram="""
    graph TD
        A[👤 User] -->|Request: Copy snapshot| B[🤖 TeamMate]
        B --> C{{"Snapshot details?" 📸}}
        C --> D[User provides details ✍️]
        D --> E[API request to AWS ☁️]
        E --> F[AWS copies snapshot 📋]
        F --> G[User receives new snapshot ID 📄]

        style A fill:#f0f9ff,stroke:#0369a1,stroke-width:2px;
        style B fill:#dbeafe,stroke:#3b82f6,stroke-width:2px;
        style C fill:#d1fae5,stroke:#059669,stroke-width:2px;
        style D fill:#bbf7d0,stroke:#16a34a,stroke-width:2px;
        style E fill:#fee2e2,stroke:#ef4444,stroke-width:2px;
        style F fill:#ffedd5,stroke:#ea580c,stroke-width:2px;
        style G fill:#e0f2fe,stroke:#0284c7,stroke-width:2px;
    """
)

tool_registry.register("aws", ebs_create_volume)
tool_registry.register("aws", ebs_delete_volume)
tool_registry.register("aws", ebs_attach_volume)
tool_registry.register("aws", ebs_detach_volume)
tool_registry.register("aws", ebs_list_volumes)
tool_registry.register("aws", ebs_create_snapshot)
tool_registry.register("aws", ebs_delete_snapshot)
tool_registry.register("aws", ebs_list_snapshots)
tool_registry.register("aws", ebs_copy_snapshot) 