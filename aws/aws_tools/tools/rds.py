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

tool_registry.register("aws", rds_create_instance)
tool_registry.register("aws", rds_delete_instance)
tool_registry.register("aws", rds_describe_instances)
tool_registry.register("aws", rds_start_instance)
tool_registry.register("aws", rds_stop_instance)
tool_registry.register("aws", rds_create_snapshot)
tool_registry.register("aws", rds_list_snapshots)