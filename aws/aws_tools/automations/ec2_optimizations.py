from kubiya_sdk.tools import Arg
from ..tools.base import AWSCliTool
from kubiya_sdk.tools.registry import tool_registry

auto_ec2_cost_optimization = AWSCliTool(
    name="auto_ec2_cost_optimization",
    description="Automate EC2 cost optimization",
    content="""
    #!/bin/bash
    set -e
    
    # Get EC2 instances
    instances=$(aws ec2 describe-instances --query 'Reservations[].Instances[].InstanceId' --output text)
    
    # Get cost data
    cost_data=$(aws ce get-cost-and-usage --time-period Start=$start_date,End=$end_date --granularity DAILY --metrics BlendedCost --group-by Type=DIMENSION,Key=INSTANCE_TYPE)
    
    # Analyze and optimize (simplified example)
    for instance in $instances; do
        utilization=$(aws cloudwatch get-metric-statistics --namespace AWS/EC2 --metric-name CPUUtilization --start-time $start_date --end-time $end_date --period 86400 --statistics Average --dimensions Name=InstanceId,Value=$instance --query 'Datapoints[].Average' --output text)
        
        if (( $(echo "$utilization < 10" | bc -l) )); then
            echo "Low utilization detected for instance $instance. Stopping instance."
            aws ec2 stop-instances --instance-ids $instance
        fi
    done
    
    echo "Cost optimization complete. Please review the results."
    """,
    args=[
        Arg(name="start_date", type="str", description="Start date for analysis (YYYY-MM-DD)", required=True),
        Arg(name="end_date", type="str", description="End date for analysis (YYYY-MM-DD)", required=True),
    ],
)

tool_registry.register("aws", auto_ec2_cost_optimization)