from kubiya_sdk.tools import Arg
from .base import AWSCliTool
from kubiya_sdk.tools.registry import tool_registry

cloudwatch_get_metric_statistics = AWSCliTool(
    name="cloudwatch_get_metric_statistics",
    description="Get CloudWatch metric statistics",
    content="""
    aws cloudwatch get-metric-statistics \\
        --namespace $namespace \\
        --metric-name $metric_name \\
        --dimensions Name=$dimension_name,Value=$dimension_value \\
        --start-time $(date -d "-$start_time_offset minutes" -u +"%Y-%m-%dT%H:%M:%SZ") \\
        --end-time $(date -u +"%Y-%m-%dT%H:%M:%SZ") \\
        --period $period \\
        --statistics Average Maximum Minimum
    """,
    args=[
        Arg(name="namespace", type="str", description="CloudWatch namespace (e.g., 'AWS/EC2')", required=True),
        Arg(name="metric_name", type="str", description="Metric name (e.g., 'CPUUtilization')", required=True),
        Arg(name="dimension_name", type="str", description="Dimension name (e.g., 'ServiceName')", required=True),
        Arg(name="dimension_value", type="str", description="Dimension value (e.g., 'worker')", required=True),
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
    aws autoscaling describe-scaling-activities \\
        --auto-scaling-group-name $asg_name \\
        --max-records 100
    
    # Get CPU utilization metrics
    aws cloudwatch get-metric-statistics \\
        --namespace AWS/EC2 \\
        --metric-name CPUUtilization \\
        --dimensions Name=AutoScalingGroupName,Value=$asg_name \\
        --start-time $(date -d "-$hours hours" -u +"%Y-%m-%dT%H:%M:%SZ") \\
        --end-time $(date -u +"%Y-%m-%dT%H:%M:%SZ") \\
        --period 300 \\
        --statistics Average
    """,
    args=[
        Arg(name="asg_name", type="str", description="Auto Scaling Group name", required=True),
        Arg(name="hours", type="int", description="Hours of history to analyze", required=True),
    ],
)

tool_registry.register("aws", cloudwatch_get_metric_statistics)
tool_registry.register("aws", cloudwatch_analyze_autoscaling) 