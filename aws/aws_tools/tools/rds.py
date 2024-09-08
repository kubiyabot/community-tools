from kubiya_sdk.tools import Arg
from .base import AWSCliTool
from kubiya_sdk.tools.registry import tool_registry

rds_tool = AWSCliTool(
    name="rds",
    description="Comprehensive RDS database management",
    content="""
    #!/bin/bash
    set -e
    case "$action" in
        create)
            aws rds create-db-instance --db-instance-identifier $identifier --db-instance-class $instance_class --engine $engine --master-username $username --master-user-password $password --allocated-storage $storage
            ;;
        delete)
            aws rds delete-db-instance --db-instance-identifier $identifier --skip-final-snapshot
            ;;
        describe)
            aws rds describe-db-instances $([[ -n "$identifier" ]] && echo "--db-instance-identifier $identifier")
            ;;
        modify)
            aws rds modify-db-instance --db-instance-identifier $identifier $([[ -n "$new_class" ]] && echo "--db-instance-class $new_class") $([[ -n "$new_storage" ]] && echo "--allocated-storage $new_storage")
            ;;
        start)
            aws rds start-db-instance --db-instance-identifier $identifier
            ;;
        stop)
            aws rds stop-db-instance --db-instance-identifier $identifier
            ;;
        create-snapshot)
            aws rds create-db-snapshot --db-instance-identifier $identifier --db-snapshot-identifier $snapshot_id
            ;;
        list-snapshots)
            aws rds describe-db-snapshots $([[ -n "$identifier" ]] && echo "--db-instance-identifier $identifier")
            ;;
        *)
            echo "Invalid action"
            exit 1
            ;;
    esac
    """,
    args=[
        Arg(name="action", type="str", description="Action to perform", required=True),
        Arg(name="identifier", type="str", description="RDS instance identifier", required=False),
        Arg(name="instance_class", type="str", description="RDS instance class", required=False),
        Arg(name="engine", type="str", description="Database engine", required=False),
        Arg(name="username", type="str", description="Master username", required=False),
        Arg(name="password", type="str", description="Master password", required=False),
        Arg(name="storage", type="int", description="Allocated storage in GB", required=False),
        Arg(name="new_class", type="str", description="New instance class for modification", required=False),
        Arg(name="new_storage", type="int", description="New storage size for modification", required=False),
        Arg(name="snapshot_id", type="str", description="Snapshot identifier", required=False),
    ],
)

tool_registry.register("aws", rds_tool)