from kubiya_sdk.tools import Arg
from .base import AWSCliTool, AWSSdkTool
from kubiya_sdk.tools.registry import tool_registry

ec2_describe_instances = AWSCliTool(
    name="ec2_describe_instances",
    description="Describe EC2 instances",
    content="aws ec2 describe-instances $([[ -n \"$instance_ids\" ]] && echo \"--instance-ids $instance_ids\")",
    args=[
        Arg(name="instance_ids", type="str", description="Comma-separated list of instance IDs (e.g., 'i-1234567890abcdef0,i-0987654321fedcba0')", required=False),
    ],
    mermaid_diagram="""
    graph TD
        A[👤 User] -->|Ask: List EC2 instances| B[🤖 TeamMate]
        B --> C{{"Region?" 🌍}}
        C --> D[User specifies region ✍️]
        D --> E[API request to AWS ☁️]
        E --> F[AWS retrieves EC2 instances 📦]
        F --> G[Convert to readable format 📝]
        G --> H[User gets EC2 instance list 📄]

        style A fill:#f0f9ff,stroke:#0369a1,stroke-width:2px;
        style B fill:#dbeafe,stroke:#3b82f6,stroke-width:2px;
        style C fill:#d1fae5,stroke:#059669,stroke-width:2px;
        style D fill:#bbf7d0,stroke:#16a34a,stroke-width:2px;
        style E fill:#fee2e2,stroke:#ef4444,stroke-width:2px;
        style F fill:#ffedd5,stroke:#ea580c,stroke-width:2px;
        style G fill:#fef08a,stroke:#ca8a04,stroke-width:2px;
        style H fill:#e0f2fe,stroke:#0284c7,stroke-width:2px;
    """
)

ec2_start_instance = AWSCliTool(
    name="ec2_start_instance",
    description="Start an EC2 instance",
    content="aws ec2 start-instances --instance-ids $instance_id",
    args=[
        Arg(name="instance_id", type="str", description="Instance ID to start (e.g., 'i-1234567890abcdef0')", required=True),
    ],
    mermaid_diagram="""
    graph TD
        A[👤 User] -->|Request: Start EC2 instance| B[🤖 TeamMate]
        B --> C{{"Instance ID?" 🔢}}
        C --> D[User provides instance ID ✍️]
        D --> E[API request to AWS ☁️]
        E --> F[AWS starts the EC2 instance 🚀]
        F --> G[Instance state changes to 'running' ✅]
        G --> H[User notified of successful start 📢]

        style A fill:#f0f9ff,stroke:#0369a1,stroke-width:2px;
        style B fill:#dbeafe,stroke:#3b82f6,stroke-width:2px;
        style C fill:#d1fae5,stroke:#059669,stroke-width:2px;
        style D fill:#bbf7d0,stroke:#16a34a,stroke-width:2px;
        style E fill:#fee2e2,stroke:#ef4444,stroke-width:2px;
        style F fill:#ffedd5,stroke:#ea580c,stroke-width:2px;
        style G fill:#fef08a,stroke:#ca8a04,stroke-width:2px;
        style H fill:#e0f2fe,stroke:#0284c7,stroke-width:2px;
    """
)

ec2_stop_instance = AWSCliTool(
    name="ec2_stop_instance",
    description="Stop an EC2 instance",
    content="aws ec2 stop-instances --instance-ids $instance_id",
    args=[
        Arg(name="instance_id", type="str", description="Instance ID to stop (e.g., 'i-1234567890abcdef0')", required=True),
    ],
    mermaid_diagram="""
    graph TD
        A[👤 User] -->|Request: Stop EC2 instance| B[🤖 TeamMate]
        B --> C{{"Instance ID?" 🔢}}
        C --> D[User provides instance ID ✍️]
        D --> E[API request to AWS ☁️]
        E --> F[AWS stops the EC2 instance 🛑]
        F --> G[Instance state changes to 'stopped' ⏹️]
        G --> H[User notified of successful stop 📢]

        style A fill:#f0f9ff,stroke:#0369a1,stroke-width:2px;
        style B fill:#dbeafe,stroke:#3b82f6,stroke-width:2px;
        style C fill:#d1fae5,stroke:#059669,stroke-width:2px;
        style D fill:#bbf7d0,stroke:#16a34a,stroke-width:2px;
        style E fill:#fee2e2,stroke:#ef4444,stroke-width:2px;
        style F fill:#ffedd5,stroke:#ea580c,stroke-width:2px;
        style G fill:#fef08a,stroke:#ca8a04,stroke-width:2px;
        style H fill:#e0f2fe,stroke:#0284c7,stroke-width:2px;
    """
)

ec2_get_console_output = AWSCliTool(
    name="ec2_get_console_output",
    description="Get console output of an EC2 instance",
    content="aws ec2 get-console-output --instance-id $instance_id",
    args=[
        Arg(name="instance_id", type="str", description="Instance ID to get console output from (e.g., 'i-1234567890abcdef0')", required=True),
    ],
    mermaid_diagram="""
    graph TD
        A[👤 User] -->|Request: Get EC2 console output| B[🤖 TeamMate]
        B --> C{{"Instance ID?" 🔢}}
        C --> D[User provides instance ID ✍️]
        D --> E[API request to AWS ☁️]
        E --> F[AWS retrieves console output 📜]
        F --> G[Format console output 📝]
        G --> H[User receives console output 📄]

        style A fill:#f0f9ff,stroke:#0369a1,stroke-width:2px;
        style B fill:#dbeafe,stroke:#3b82f6,stroke-width:2px;
        style C fill:#d1fae5,stroke:#059669,stroke-width:2px;
        style D fill:#bbf7d0,stroke:#16a34a,stroke-width:2px;
        style E fill:#fee2e2,stroke:#ef4444,stroke-width:2px;
        style F fill:#ffedd5,stroke:#ea580c,stroke-width:2px;
        style G fill:#fef08a,stroke:#ca8a04,stroke-width:2px;
        style H fill:#e0f2fe,stroke:#0284c7,stroke-width:2px;
    """
)

ec2_describe_instance_status = AWSCliTool(
    name="ec2_describe_instance_status",
    description="Get status of EC2 instances",
    content="aws ec2 describe-instance-status $([[ -n \"$instance_ids\" ]] && echo \"--instance-ids $instance_ids\")",
    args=[
        Arg(name="instance_ids", type="str", description="Comma-separated list of instance IDs (e.g., 'i-1234567890abcdef0,i-0987654321fedcba0')", required=False),
    ],
    mermaid_diagram="""
    graph TD
        A[👤 User] -->|Request: Get EC2 instance status| B[🤖 TeamMate]
        B --> C{{"Instance IDs?" 🔢}}
        C --> D[User provides instance IDs ✍️]
        D --> E[API request to AWS ☁️]
        E --> F[AWS retrieves instance status 📊]
        F --> G[Format status information 📝]
        G --> H[User receives instance status 📄]

        style A fill:#f0f9ff,stroke:#0369a1,stroke-width:2px;
        style B fill:#dbeafe,stroke:#3b82f6,stroke-width:2px;
        style C fill:#d1fae5,stroke:#059669,stroke-width:2px;
        style D fill:#bbf7d0,stroke:#16a34a,stroke-width:2px;
        style E fill:#fee2e2,stroke:#ef4444,stroke-width:2px;
        style F fill:#ffedd5,stroke:#ea580c,stroke-width:2px;
        style G fill:#fef08a,stroke:#ca8a04,stroke-width:2px;
        style H fill:#e0f2fe,stroke:#0284c7,stroke-width:2px;
    """
)

ec2_get_instance_metrics = AWSSdkTool(
    name="ec2_get_instance_metrics",
    description="Get CloudWatch metrics for an EC2 instance",
    content="""
import boto3
from datetime import datetime, timedelta

def get_instance_metrics(instance_id, metric_name, period):
    cloudwatch = boto3.client('cloudwatch')
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=1)

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

result = get_instance_metrics(instance_id, metric_name, period)
print(result)
    """,
    args=[
        Arg(name="instance_id", type="str", description="Instance ID to get metrics for (e.g., 'i-1234567890abcdef0')", required=True),
        Arg(name="metric_name", type="str", description="Metric name (e.g., 'CPUUtilization', 'NetworkIn', 'DiskReadOps')", required=True),
        Arg(name="period", type="int", description="Period in seconds (e.g., 300 for 5-minute intervals)", required=True),
    ],
    mermaid_diagram="""
    graph TD
        A[👤 User] -->|Request: Get EC2 metrics| B[🤖 TeamMate]
        B --> C{{"Instance ID, Metric, Period?" 🔢}}
        C --> D[User provides details ✍️]
        D --> E[API request to AWS CloudWatch ☁️]
        E --> F[AWS retrieves metric data 📊]
        F --> G[Process and format metric data 📝]
        G --> H[User receives metric information 📈]

        style A fill:#f0f9ff,stroke:#0369a1,stroke-width:2px;
        style B fill:#dbeafe,stroke:#3b82f6,stroke-width:2px;
        style C fill:#d1fae5,stroke:#059669,stroke-width:2px;
        style D fill:#bbf7d0,stroke:#16a34a,stroke-width:2px;
        style E fill:#fee2e2,stroke:#ef4444,stroke-width:2px;
        style F fill:#ffedd5,stroke:#ea580c,stroke-width:2px;
        style G fill:#fef08a,stroke:#ca8a04,stroke-width:2px;
        style H fill:#e0f2fe,stroke:#0284c7,stroke-width:2px;
    """
)

ec2_describe_instance_types = AWSCliTool(
    name="ec2_describe_instance_types",
    description="Describe EC2 instance types",
    content="aws ec2 describe-instance-types --instance-types $instance_type",
    args=[
        Arg(name="instance_type", type="str", description="Instance type to describe (e.g., 't2.micro', 'm5.large')", required=True),
    ],
    mermaid_diagram="""
    graph TD
        A[👤 User] -->|Request: Describe EC2 instance type| B[🤖 TeamMate]
        B --> C{{"Instance Type?" 🖥️}}
        C --> D[User provides instance type ✍️]
        D --> E[API request to AWS ☁️]
        E --> F[AWS retrieves instance type details 📋]
        F --> G[Format instance type information 📝]
        G --> H[User receives instance type details 📄]

        style A fill:#f0f9ff,stroke:#0369a1,stroke-width:2px;
        style B fill:#dbeafe,stroke:#3b82f6,stroke-width:2px;
        style C fill:#d1fae5,stroke:#059669,stroke-width:2px;
        style D fill:#bbf7d0,stroke:#16a34a,stroke-width:2px;
        style E fill:#fee2e2,stroke:#ef4444,stroke-width:2px;
        style F fill:#ffedd5,stroke:#ea580c,stroke-width:2px;
        style G fill:#fef08a,stroke:#ca8a04,stroke-width:2px;
        style H fill:#e0f2fe,stroke:#0284c7,stroke-width:2px;
    """
)

ec2_get_instance_tags = AWSCliTool(
    name="ec2_get_instance_tags",
    description="Get tags for an EC2 instance",
    content="aws ec2 describe-tags --filters \"Name=resource-id,Values=$instance_id\"",
    args=[
        Arg(name="instance_id", type="str", description="Instance ID to get tags for (e.g., 'i-1234567890abcdef0')", required=True),
    ],
    mermaid_diagram="""
    graph TD
        A[👤 User] -->|Request: Get EC2 instance tags| B[🤖 TeamMate]
        B --> C{{"Instance ID?" 🔢}}
        C --> D[User provides instance ID ✍️]
        D --> E[API request to AWS ☁️]
        E --> F[AWS retrieves instance tags 🏷️]
        F --> G[Format tag information 📝]
        G --> H[User receives instance tags 📄]

        style A fill:#f0f9ff,stroke:#0369a1,stroke-width:2px;
        style B fill:#dbeafe,stroke:#3b82f6,stroke-width:2px;
        style C fill:#d1fae5,stroke:#059669,stroke-width:2px;
        style D fill:#bbf7d0,stroke:#16a34a,stroke-width:2px;
        style E fill:#fee2e2,stroke:#ef4444,stroke-width:2px;
        style F fill:#ffedd5,stroke:#ea580c,stroke-width:2px;
        style G fill:#fef08a,stroke:#ca8a04,stroke-width:2px;
        style H fill:#e0f2fe,stroke:#0284c7,stroke-width:2px;
    """
)

tool_registry.register("aws", ec2_describe_instances)
tool_registry.register("aws", ec2_start_instance)
tool_registry.register("aws", ec2_stop_instance)
tool_registry.register("aws", ec2_get_console_output)
tool_registry.register("aws", ec2_describe_instance_status)
tool_registry.register("aws", ec2_get_instance_metrics)
tool_registry.register("aws", ec2_describe_instance_types)
tool_registry.register("aws", ec2_get_instance_tags)