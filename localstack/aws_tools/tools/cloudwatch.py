from kubiya_sdk.tools import Arg
from .base import AWSCliTool
from kubiya_sdk.tools.registry import tool_registry

def format_dimensions(dimensions):
    """
    Convert dimensions from various formats to AWS CLI format.
    Accepts:
    - String in format "Name=key,Value=value Name=key2,Value=value2"
    - String in format "key=value,key2=value2"
    - Dict in format {"key": "value", "key2": "value2"}
    """
    if not dimensions:
        return ""
    
    # If already in correct format, return as is
    if isinstance(dimensions, str) and "Name=" in dimensions and "Value=" in dimensions:
        return dimensions
        
    # Convert string format "key=value,key2=value2" to dict
    if isinstance(dimensions, str) and "Name=" not in dimensions:
        dim_dict = {}
        for pair in dimensions.split():
            for kv in pair.split(','):
                if '=' in kv:
                    k, v = kv.split('=', 1)
                    dim_dict[k] = v
        dimensions = dim_dict
    
    # Convert dict to AWS CLI format
    if isinstance(dimensions, dict):
        return ' '.join([f"Name={k},Value={v}" for k, v in dimensions.items()])
    
    raise ValueError("Invalid dimensions format")

cloudwatch_get_metric_statistics = AWSCliTool(
    name="cloudwatch_get_metric_statistics",
    description="Get CloudWatch metric statistics",
    content="""
    FORMATTED_DIMENSIONS=$(python3 -c "
from cloudwatch import format_dimensions
print(format_dimensions('$dimensions'))
")
    
    aws cloudwatch get-metric-statistics \
        --namespace $namespace \
        --metric-name $metric_name \
        --dimensions $FORMATTED_DIMENSIONS \
        --start-time $(date -d "-$start_time_offset minutes" -u +"%Y-%m-%dT%H:%M:%SZ") \
        --end-time $(date -u +"%Y-%m-%dT%H:%M:%SZ") \
        --period $period \
        --statistics Average Maximum Minimum
    """,
    args=[
        Arg(name="namespace", type="str", description="CloudWatch namespace (e.g., 'AWS/EC2')", required=True),
        Arg(name="metric_name", type="str", description="Metric name (e.g., 'CPUUtilization')", required=True),
        Arg(name="dimensions", type="str", description="Dimensions in any format (e.g., 'ServiceName=worker,ClusterName=prod' or 'Name=ServiceName,Value=worker Name=ClusterName,Value=prod')", required=True),
        Arg(name="period", type="int", description="Period in seconds", required=True),
        Arg(name="start_time_offset", type="int", description="Start time offset in minutes", required=True),
    ],
)

cloudwatch_analyze_autoscaling = AWSCliTool(
    name="cloudwatch_analyze_autoscaling",
    description="Analyze AutoScaling behavior",
    content="""
    # Get ASG details
    aws autoscaling describe-auto-scaling-groups --auto-scaling-group-names $asg_name
    
    # Get scaling activities
    aws autoscaling describe-scaling-activities \
        --auto-scaling-group-name $asg_name \
        --max-records 100
    
    # Get CPU utilization metrics
    aws cloudwatch get-metric-statistics \
        --namespace AWS/EC2 \
        --metric-name CPUUtilization \
        --dimensions Name=AutoScalingGroupName,Value=$asg_name \
        --start-time $(date -d "-$hours hours" -u +"%Y-%m-%dT%H:%M:%SZ") \
        --end-time $(date -u +"%Y-%m-%dT%H:%M:%SZ") \
        --period 300 \
        --statistics Average
    """,
    args=[
        Arg(name="asg_name", type="str", description="Auto Scaling Group name", required=True),
        Arg(name="hours", type="int", description="Hours of history to analyze", required=True),
    ],
)

tool_registry.register("aws", cloudwatch_get_metric_statistics)
tool_registry.register("aws", cloudwatch_analyze_autoscaling) 