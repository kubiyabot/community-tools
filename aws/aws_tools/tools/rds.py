from kubiya_sdk.tools import Arg
from .base import AWSCliTool
from kubiya_sdk.tools.registry import tool_registry

rds_create_instance = AWSCliTool(
    name="rds_create_instance",
    description="Create a new RDS instance",
    content="""
    aws rds create-db-instance --db-instance-identifier $identifier --db-instance-class $instance_class --engine $engine --master-username $username --master-user-password $password --allocated-storage $storage
    """,
    args=[
        Arg(name="identifier", type="str", description="RDS instance identifier (e.g., 'mydb')", required=True),
        Arg(name="instance_class", type="str", description="RDS instance class (e.g., 'db.t3.micro')", required=True),
        Arg(name="engine", type="str", description="Database engine (e.g., 'mysql', 'postgres')", required=True),
        Arg(name="username", type="str", description="Master username", required=True),
        Arg(name="password", type="str", description="Master password", required=True),
        Arg(name="storage", type="int", description="Allocated storage in GB (e.g., 20)", required=True),
    ],
)

rds_delete_instance = AWSCliTool(
    name="rds_delete_instance",
    description="Delete an RDS instance",
    content="""
    aws rds delete-db-instance --db-instance-identifier $identifier --skip-final-snapshot
    """,
    args=[
        Arg(name="identifier", type="str", description="RDS instance identifier to delete (e.g., 'mydb')", required=True),
    ],
)

rds_describe_instances = AWSCliTool(
    name="rds_describe_instances",
    description="Describe RDS instances",
    content="""
    aws rds describe-db-instances $([[ -n "$identifier" ]] && echo "--db-instance-identifier $identifier")
    """,
    args=[
        Arg(name="identifier", type="str", description="RDS instance identifier to describe (optional)", required=False),
    ],
)

rds_start_instance = AWSCliTool(
    name="rds_start_instance",
    description="Start an RDS instance",
    content="""
    aws rds start-db-instance --db-instance-identifier $identifier
    """,
    args=[
        Arg(name="identifier", type="str", description="RDS instance identifier to start (e.g., 'mydb')", required=True),
    ],
)

rds_stop_instance = AWSCliTool(
    name="rds_stop_instance",
    description="Stop an RDS instance",
    content="""
    aws rds stop-db-instance --db-instance-identifier $identifier
    """,
    args=[
        Arg(name="identifier", type="str", description="RDS instance identifier to stop (e.g., 'mydb')", required=True),
    ],
)

rds_create_snapshot = AWSCliTool(
    name="rds_create_snapshot",
    description="Create a snapshot of an RDS instance",
    content="""
    aws rds create-db-snapshot --db-instance-identifier $identifier --db-snapshot-identifier $snapshot_id
    """,
    args=[
        Arg(name="identifier", type="str", description="RDS instance identifier (e.g., 'mydb')", required=True),
        Arg(name="snapshot_id", type="str", description="Snapshot identifier (e.g., 'mydb-snapshot-20230101')", required=True),
    ],
)

rds_list_snapshots = AWSCliTool(
    name="rds_list_snapshots",
    description="List RDS snapshots",
    content="""
    aws rds describe-db-snapshots $([[ -n "$identifier" ]] && echo "--db-instance-identifier $identifier")
    """,
    args=[
        Arg(name="identifier", type="str", description="RDS instance identifier to filter snapshots (optional)", required=False),
    ],
)

rds_describe_events = AWSCliTool(
    name="rds_describe_events",
    description="List RDS events from the past 24 hours",
    content="aws rds describe-events --duration 1440",
    args=[],
    mermaid_diagram="""
    graph TD
        A[👤 User] -->|Request: List RDS events| B[🤖 TeamMate]
        B --> C[API request to AWS ☁️]
        C --> D[AWS retrieves events 📅]
        D --> E[User receives event list 📄]

        style A fill:#f0f9ff,stroke:#0369a1,stroke-width:2px;
        style B fill:#dbeafe,stroke:#3b82f6,stroke-width:2px;
        style C fill:#fee2e2,stroke:#ef4444,stroke-width:2px;
        style D fill:#ffedd5,stroke:#ea580c,stroke-width:2px;
        style E fill:#e0f2fe,stroke:#0284c7,stroke-width:2px;
    """
)

rds_describe_db_parameters = AWSCliTool(
    name="rds_describe_db_parameters",
    description="Describe database parameters for an RDS instance",
    content="aws rds describe-db-parameters --db-parameter-group-name $parameter_group",
    args=[
        Arg(name="parameter_group", type="str", description="Name of the DB parameter group", required=True),
    ],
    mermaid_diagram="""
    graph TD
        A[👤 User] -->|Request: Get DB parameters| B[🤖 TeamMate]
        B --> C{{"Parameter group?" 🔢}}
        C --> D[User provides group name ✍️]
        D --> E[API request to AWS ☁️]
        E --> F[AWS retrieves parameters ⚙️]
        F --> G[User receives parameter list 📄]

        style A fill:#f0f9ff,stroke:#0369a1,stroke-width:2px;
        style B fill:#dbeafe,stroke:#3b82f6,stroke-width:2px;
        style C fill:#d1fae5,stroke:#059669,stroke-width:2px;
        style D fill:#bbf7d0,stroke:#16a34a,stroke-width:2px;
        style E fill:#fee2e2,stroke:#ef4444,stroke-width:2px;
        style F fill:#ffedd5,stroke:#ea580c,stroke-width:2px;
        style G fill:#e0f2fe,stroke:#0284c7,stroke-width:2px;
    """
)

rds_describe_backups = AWSCliTool(
    name="rds_describe_backups",
    description="List automated backups for an RDS instance",
    content="aws rds describe-db-instance-automated-backups --db-instance-identifier $identifier",
    args=[
        Arg(name="identifier", type="str", description="RDS instance identifier", required=True),
    ],
    mermaid_diagram="""
    graph TD
        A[👤 User] -->|Request: List backups| B[🤖 TeamMate]
        B --> C{{"Instance ID?" 🔢}}
        C --> D[User provides instance ID ✍️]
        D --> E[API request to AWS ☁️]
        E --> F[AWS retrieves backup list 💾]
        F --> G[User receives backup information 📄]

        style A fill:#f0f9ff,stroke:#0369a1,stroke-width:2px;
        style B fill:#dbeafe,stroke:#3b82f6,stroke-width:2px;
        style C fill:#d1fae5,stroke:#059669,stroke-width:2px;
        style D fill:#bbf7d0,stroke:#16a34a,stroke-width:2px;
        style E fill:#fee2e2,stroke:#ef4444,stroke-width:2px;
        style F fill:#ffedd5,stroke:#ea580c,stroke-width:2px;
        style G fill:#e0f2fe,stroke:#0284c7,stroke-width:2px;
    """
)

tool_registry.register("aws", rds_create_instance)
tool_registry.register("aws", rds_delete_instance)
tool_registry.register("aws", rds_describe_instances)
tool_registry.register("aws", rds_start_instance)
tool_registry.register("aws", rds_stop_instance)
tool_registry.register("aws", rds_create_snapshot)
tool_registry.register("aws", rds_list_snapshots)
tool_registry.register("aws", rds_describe_events)
tool_registry.register("aws", rds_describe_db_parameters)
tool_registry.register("aws", rds_describe_backups)