from kubiya_sdk.tools import Arg
from .base import AWSCliTool
from kubiya_sdk.tools.registry import tool_registry

s3_tool = AWSCliTool(
    name="s3",
    description="Comprehensive S3 bucket and object management",
    content="""
    #!/bin/bash
    set -e
    case "$action" in
        ls)
            aws s3 ls $([[ -n "$bucket" ]] && echo "s3://$bucket/$prefix")
            ;;
        cp)
            aws s3 cp $source $destination $([[ -n "$options" ]] && echo "$options")
            ;;
        mv)
            aws s3 mv $source $destination $([[ -n "$options" ]] && echo "$options")
            ;;
        rm)
            aws s3 rm $target $([[ -n "$options" ]] && echo "$options")
            ;;
        sync)
            aws s3 sync $source $destination $([[ -n "$options" ]] && echo "$options")
            ;;
        mb)
            aws s3 mb s3://$bucket
            ;;
        rb)
            aws s3 rb s3://$bucket $([[ "$force" == "true" ]] && echo "--force")
            ;;
        presign)
            aws s3 presign s3://$bucket/$key --expires-in $expiration
            ;;
        website)
            aws s3 website s3://$bucket --index-document $index --error-document $error
            ;;
        *)
            echo "Invalid action"
            exit 1
            ;;
    esac
    """,
    args=[
        Arg(name="action", type="str", description="Action to perform", required=True),
        Arg(name="bucket", type="str", description="S3 bucket name", required=False),
        Arg(name="prefix", type="str", description="S3 prefix", required=False),
        Arg(name="source", type="str", description="Source path", required=False),
        Arg(name="destination", type="str", description="Destination path", required=False),
        Arg(name="target", type="str", description="Target path for removal", required=False),
        Arg(name="options", type="str", description="Additional options", required=False),
        Arg(name="force", type="bool", description="Force removal of non-empty bucket", required=False),
        Arg(name="key", type="str", description="S3 object key for presigning", required=False),
        Arg(name="expiration", type="int", description="Presigned URL expiration in seconds", required=False),
        Arg(name="index", type="str", description="Index document for static website", required=False),
        Arg(name="error", type="str", description="Error document for static website", required=False),
    ],
)

tool_registry.register("aws", s3_tool)