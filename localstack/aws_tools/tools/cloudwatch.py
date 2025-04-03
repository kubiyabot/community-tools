from kubiya_sdk.tools import Arg
from .base import AWSCliTool
from kubiya_sdk.tools.registry import tool_registry

cloudwatch_get_metric_statistics = AWSCliTool(
    name="cloudwatch_get_metric_statistics",
    description="Get CloudWatch metric statistics (using get-metric-data for LocalStack compatibility)",
    content="""
# Calculate time range
START_TIME=$(date -d "-$start_time_offset minutes" -u +"%Y-%m-%dT%H:%M:%SZ")
END_TIME=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Use get-metric-data for better support in LocalStack
aws cloudwatch get-metric-data \\
  --metric-data-queries '[{
    "Id": "m1",
    "MetricStat": {
      "Metric": {
        "Namespace": "'$namespace'",
        "MetricName": "'$metric_name'",
        "Dimensions": [
          { "Name": "'$dimension_name'", "Value": "'$dimension_value'" }
        ]
      },
      "Period": '$period',
      "Stat": "Average"
    },
    "ReturnData": true
  }]' \\
  --start-time "$START_TIME" \\
  --end-time "$END_TIME"
""",
    args=[
        Arg(name="namespace", type="str", description="CloudWatch namespace (e.g., 'AWS/ECS')", required=True),
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