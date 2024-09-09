from kubiya_sdk.tools import Arg
from ..tools.base import AWSCliTool, AWSSdkTool
from kubiya_sdk.tools.registry import tool_registry

auto_ec2_cost_optimization = AWSCliTool(
    name="auto_ec2_cost_optimization",
    description="Automate EC2 cost optimization",
    content="""
    #!/bin/bash
    set -e
    
    instances=$(aws ec2 describe-instances --filters "Name=instance-state-name,Values=running" --query 'Reservations[].Instances[].InstanceId' --output text)
    
    for instance in $instances; do
        utilization=$(aws cloudwatch get-metric-statistics --namespace AWS/EC2 --metric-name CPUUtilization --start-time $start_date --end-time $end_date --period 86400 --statistics Average --dimensions Name=InstanceId,Value=$instance --query 'Datapoints[].Average' --output text)
        
        if (( $(echo "$utilization < $utilization_threshold" | bc -l) )); then
            echo "Low utilization detected for instance $instance. Performing action: $low_utilization_action"
            case $low_utilization_action in
                stop)
                    aws ec2 stop-instances --instance-ids $instance
                    ;;
                terminate)
                    aws ec2 terminate-instances --instance-ids $instance
                    ;;
                notify)
                    echo "Notification: Low utilization for instance $instance"
                    ;;
            esac
        fi
    done
    
    echo "Short-term cost optimization complete."
    """,
    args=[
        Arg(name="start_date", type="str", description="Start date for analysis (YYYY-MM-DD)", required=True),
        Arg(name="end_date", type="str", description="End date for analysis (YYYY-MM-DD)", required=True),
        Arg(name="utilization_threshold", type="float", description="CPU utilization threshold for action", required=True),
        Arg(name="low_utilization_action", type="str", description="Action to take on low utilization (stop/terminate/notify)", required=True),
    ],
)

ec2_long_running_optimization = AWSSdkTool(
    name="ec2_long_running_optimization",
    description="Long-running EC2 optimization and monitoring",
    content="""
import boto3
import time
from datetime import datetime, timedelta

def get_instance_metrics(instance_id, metric_name, start_time, end_time, period):
    cloudwatch = boto3.client('cloudwatch')
    response = cloudwatch.get_metric_statistics(
        Namespace='AWS/EC2',
        MetricName=metric_name,
        Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
        StartTime=start_time,
        EndTime=end_time,
        Period=period,
        Statistics=['Average']
    )
    return response['Datapoints']

def get_instances():
    ec2 = boto3.resource('ec2')
    return list(ec2.instances.filter(Filters=[{'Name': 'instance-state-name', 'Values': ['running']}]))

def perform_action(instance, action):
    if action == 'stop':
        instance.stop()
    elif action == 'terminate':
        instance.terminate()
    elif action == 'notify':
        print(f"Notification: Action required for instance {instance.id}")
    # Add more actions as needed

def optimize_instances(instances, utilization_threshold, action):
    for instance in instances:
        cpu_utilization = get_instance_metrics(instance.id, 'CPUUtilization', datetime.utcnow() - timedelta(days=1), datetime.utcnow(), 3600)
        avg_cpu = sum(datapoint['Average'] for datapoint in cpu_utilization) / len(cpu_utilization) if cpu_utilization else 0
        
        if avg_cpu < utilization_threshold:
            print(f"Low utilization detected for instance {instance.id} (CPU: {avg_cpu:.2f}%)")
            perform_action(instance, action)

def resize_instances(instances, resize_threshold, resize_action):
    for instance in instances:
        cpu_utilization = get_instance_metrics(instance.id, 'CPUUtilization', datetime.utcnow() - timedelta(days=7), datetime.utcnow(), 3600)
        avg_cpu = sum(datapoint['Average'] for datapoint in cpu_utilization) / len(cpu_utilization) if cpu_utilization else 0
        
        if avg_cpu < resize_threshold:
            if resize_action == 'downsize':
                new_type = get_smaller_instance_type(instance.instance_type)
                if new_type:
                    print(f"Resizing instance {instance.id} from {instance.instance_type} to {new_type} (Avg CPU: {avg_cpu:.2f}%)")
                    instance.modify_attribute(InstanceType={'Value': new_type})
            elif resize_action == 'notify':
                print(f"Notification: Consider resizing instance {instance.id} (Avg CPU: {avg_cpu:.2f}%)")

def get_smaller_instance_type(current_type):
    instance_types = ['t2.nano', 't2.micro', 't2.small', 't2.medium', 't2.large']
    try:
        current_index = instance_types.index(current_type)
        if current_index > 0:
            return instance_types[current_index - 1]
    except ValueError:
        pass
    return None

def monitor_instances(instances, duration_hours, cpu_threshold, spike_action):
    end_time = datetime.utcnow() + timedelta(hours=duration_hours)
    while datetime.utcnow() < end_time:
        for instance in instances:
            cpu_utilization = get_instance_metrics(instance.id, 'CPUUtilization', datetime.utcnow() - timedelta(minutes=5), datetime.utcnow(), 300)
            if cpu_utilization:
                latest_cpu = cpu_utilization[-1]['Average']
                if latest_cpu > cpu_threshold:
                    print(f"High CPU utilization detected for instance {instance.id}: {latest_cpu:.2f}%")
                    perform_action(instance, spike_action)
        time.sleep(300)  # Wait for 5 minutes before next check

# Main execution
instances = get_instances()
optimize_instances(instances, float(utilization_threshold), low_utilization_action)
resize_instances(instances, float(resize_threshold), resize_action)
monitor_instances(instances, int(duration_hours), float(cpu_spike_threshold), cpu_spike_action)

print("Long-running EC2 cost optimization and monitoring complete.")
    """,
    args=[
        Arg(name="duration_hours", type="int", description="Duration of monitoring in hours", required=True),
        Arg(name="utilization_threshold", type="float", description="CPU utilization threshold for optimization", required=True),
        Arg(name="low_utilization_action", type="str", description="Action for low utilization (stop/terminate/notify)", required=True),
        Arg(name="resize_threshold", type="float", description="CPU utilization threshold for resizing", required=True),
        Arg(name="resize_action", type="str", description="Action for resizing (downsize/notify)", required=True),
        Arg(name="cpu_spike_threshold", type="float", description="CPU threshold for spike detection", required=True),
        Arg(name="cpu_spike_action", type="str", description="Action for CPU spikes (notify/stop)", required=True),
    ],
    long_running=True
)

ec2_rightsizing_recommendation = AWSSdkTool(
    name="ec2_rightsizing_recommendation",
    description="Get EC2 rightsizing recommendations and optionally apply them",
    content="""
import boto3
import json

def get_rightsizing_recommendation():
    ce_client = boto3.client('ce')
    response = ce_client.get_rightsizing_recommendation(
        Service='AmazonEC2',
        Configuration={
            'RecommendationTarget': 'SAME_INSTANCE_FAMILY',
            'BenefitsConsidered': True
        }
    )
    
    recommendations = response.get('RightsizingRecommendations', [])
    formatted_recommendations = []
    for rec in recommendations:
        formatted_rec = {
            'InstanceId': rec['CurrentInstance']['ResourceId'],
            'CurrentType': rec['CurrentInstance']['InstanceType'],
            'RecommendedType': rec['ModifyRecommendationDetail']['TargetInstances'][0]['InstanceType'],
            'EstimatedMonthlySavings': rec['ModifyRecommendationDetail']['TargetInstances'][0]['EstimatedMonthlySavings']['Value']
        }
        formatted_recommendations.append(formatted_rec)
    
    return formatted_recommendations

def apply_recommendations(recommendations, action):
    ec2_client = boto3.client('ec2')
    for rec in recommendations:
        if action == 'apply':
            print(f"Resizing instance {rec['InstanceId']} from {rec['CurrentType']} to {rec['RecommendedType']}")
            ec2_client.modify_instance_attribute(
                InstanceId=rec['InstanceId'],
                InstanceType={'Value': rec['RecommendedType']}
            )
        elif action == 'notify':
            print(f"Recommendation: Resize instance {rec['InstanceId']} from {rec['CurrentType']} to {rec['RecommendedType']}")

recommendations = get_rightsizing_recommendation()
print(json.dumps(recommendations, indent=2))
apply_recommendations(recommendations, recommendation_action)
    """,
    args=[
        Arg(name="recommendation_action", type="str", description="Action for recommendations (apply/notify)", required=True),
    ],
)

ec2_reserved_instance_recommendation = AWSSdkTool(
    name="ec2_reserved_instance_recommendation",
    description="Get EC2 Reserved Instance recommendations and optionally purchase",
    content="""
import boto3
import json

def get_reserved_instance_recommendations():
    ce_client = boto3.client('ce')
    response = ce_client.get_reservation_purchase_recommendation(
        Service='Amazon Elastic Compute Cloud - Compute',
        LookbackPeriodInDays='SIXTY_DAYS',
        TermInYears='ONE_YEAR'
    )
    
    recommendations = response.get('Recommendations', [])
    formatted_recommendations = []
    for rec in recommendations:
        for detail in rec.get('InstanceRecommendations', []):
            formatted_rec = {
                'InstanceType': detail['InstanceType'],
                'RecommendedNumberOfInstances': detail['RecommendedNumberOfReservedInstances'],
                'EstimatedBreakEvenInMonths': detail['EstimatedBreakEvenInMonths'],
                'EstimatedMonthlySavings': detail['EstimatedMonthlySavingsAmount']
            }
            formatted_recommendations.append(formatted_rec)
    
    return formatted_recommendations

def purchase_reserved_instances(recommendations, action):
    ec2_client = boto3.client('ec2')
    for rec in recommendations:
        if action == 'purchase':
            print(f"Purchasing {rec['RecommendedNumberOfInstances']} Reserved Instances of type {rec['InstanceType']}")
            ec2_client.purchase_reserved_instances_offering(
                InstanceCount=rec['RecommendedNumberOfInstances'],
                InstanceType=rec['InstanceType'],
                OfferingType='Standard',
                ProductDescription='Linux/UNIX',
                TermInYears=1
            )
        elif action == 'notify':
            print(f"Recommendation: Purchase {rec['RecommendedNumberOfInstances']} Reserved Instances of type {rec['InstanceType']}")

recommendations = get_reserved_instance_recommendations()
print(json.dumps(recommendations, indent=2))
purchase_reserved_instances(recommendations, recommendation_action)
    """,
    args=[
        Arg(name="recommendation_action", type="str", description="Action for recommendations (purchase/notify)", required=True),
    ],
)

ec2_scheduled_actions = AWSSdkTool(
    name="ec2_scheduled_actions",
    description="Set up scheduled start/stop actions for EC2 instances",
    content="""
import boto3
import json
from datetime import datetime, timedelta

def create_scheduled_action(instance_id, action, schedule):
    ec2_client = boto3.client('ec2')
    events_client = boto3.client('events')
    
    try:
        instance = ec2_client.describe_instances(InstanceIds=[instance_id])['Reservations'][0]['Instances'][0]
    except:
        print(f"Error: Instance {instance_id} not found.")
        return
    
    rule_name = f"{instance_id}-{action}-{schedule.replace(' ', '_')}"
    events_client.put_rule(
        Name=rule_name,
        ScheduleExpression=f"cron({schedule})",
        State='ENABLED'
    )
    
    target_input = {
        "InstanceIds": [instance_id]
    }
    events_client.put_targets(
        Rule=rule_name,
        Targets=[
            {
                'Id': '1',
                'Arn': f"arn:aws:ssm:{instance['Placement']['AvailabilityZone'][:-1]}::automation-definition/AWS-{action.capitalize()}EC2Instance",
                'Input': json.dumps(target_input)
            }
        ]
    )
    
    print(f"Scheduled {action} action created for instance {instance_id} with schedule: {schedule}")

create_scheduled_action(instance_id, action, schedule)

print("Scheduled actions set up successfully.")
    """,
    args=[
        Arg(name="instance_id", type="str", description="EC2 instance ID", required=True),
        Arg(name="action", type="str", description="Action to schedule (start or stop)", required=True),
        Arg(name="schedule", type="str", description="Cron expression for the schedule", required=True),
    ],
)

tool_registry.register("aws", auto_ec2_cost_optimization)
tool_registry.register("aws", ec2_long_running_optimization)
tool_registry.register("aws", ec2_rightsizing_recommendation)
tool_registry.register("aws", ec2_reserved_instance_recommendation)
tool_registry.register("aws", ec2_scheduled_actions)