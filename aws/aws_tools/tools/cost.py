from kubiya_sdk.tools import Arg
from .base import AWSCliTool, AWSSdkTool
from kubiya_sdk.tools.registry import tool_registry
from datetime import datetime, timedelta

def parse_time_ago(time_ago):
    now = datetime.now()
    if time_ago.endswith('d'):
        delta = timedelta(days=int(time_ago[:-1]))
    elif time_ago.endswith('m'):
        delta = timedelta(days=int(time_ago[:-1]) * 30)  # Approximate
    else:
        raise ValueError("Invalid time format. Use 'd' for days or 'm' for months (e.g., '7d', '3m')")
    return (now - delta).strftime('%Y-%m-%d')

cost_get_cost_and_usage = AWSCliTool(
    name="cost_get_cost_and_usage",
    description="Get AWS cost and usage data",
    content="aws ce get-cost-and-usage --time-period Start=$(python3 -c \"from datetime import datetime, timedelta; print(parse_time_ago('$time_ago'))\"),End=$(date +%Y-%m-%d) --granularity $granularity --metrics $metrics",
    args=[
        Arg(name="time_ago", type="str", description="Time ago (e.g., '7d' for 7 days ago, '3m' for 3 months ago)", required=True),
        Arg(name="granularity", type="str", description="Time granularity (DAILY or MONTHLY)", required=True),
        Arg(name="metrics", type="str", description="Metrics to retrieve (e.g., 'BlendedCost,UnblendedCost,UsageQuantity')", required=True),
    ],
)

cost_get_cost_forecast = AWSCliTool(
    name="cost_get_cost_forecast",
    description="Get AWS cost forecast",
    content="aws ce get-cost-forecast --time-period Start=$(date +%Y-%m-%d),End=$(date -d '+$forecast_period' +%Y-%m-%d) --metric $metric --granularity $granularity",
    args=[
        Arg(name="forecast_period", type="str", description="Forecast period (e.g., '30d' for 30 days, '3m' for 3 months)", required=True),
        Arg(name="metric", type="str", description="Metric to forecast (e.g., 'BLENDED_COST', 'UNBLENDED_COST')", required=True),
        Arg(name="granularity", type="str", description="Time granularity (DAILY or MONTHLY)", required=True),
    ],
)

cost_get_reservation_utilization = AWSCliTool(
    name="cost_get_reservation_utilization",
    description="Get AWS reservation utilization",
    content="aws ce get-reservation-utilization --time-period Start=$(python3 -c \"from datetime import datetime, timedelta; print(parse_time_ago('$time_ago'))\"),End=$(date +%Y-%m-%d) --granularity $granularity",
    args=[
        Arg(name="time_ago", type="str", description="Time ago (e.g., '7d' for 7 days ago, '3m' for 3 months ago)", required=True),
        Arg(name="granularity", type="str", description="Time granularity (DAILY or MONTHLY)", required=True),
    ],
)

cost_get_savings_plans_utilization = AWSCliTool(
    name="cost_get_savings_plans_utilization",
    description="Get AWS Savings Plans utilization",
    content="aws ce get-savings-plans-utilization --time-period Start=$(python3 -c \"from datetime import datetime, timedelta; print(parse_time_ago('$time_ago'))\"),End=$(date +%Y-%m-%d) --granularity $granularity",
    args=[
        Arg(name="time_ago", type="str", description="Time ago (e.g., '7d' for 7 days ago, '3m' for 3 months ago)", required=True),
        Arg(name="granularity", type="str", description="Time granularity (DAILY or MONTHLY)", required=True),
    ],
)

cost_get_rightsizing_recommendation = AWSSdkTool(
    name="cost_get_rightsizing_recommendation",
    description="Get AWS rightsizing recommendations",
    content="""
import boto3
from botocore.exceptions import ClientError

def get_rightsizing_recommendation(service):
    try:
        ce_client = boto3.client('ce')
        response = ce_client.get_rightsizing_recommendation(
            Service=service
        )
        return response
    except ClientError as e:
        print(f"An error occurred: {e}")
        return None

result = get_rightsizing_recommendation(service)
print(result)
    """,
    args=[
        Arg(name="service", type="str", description="AWS service to get recommendations for (e.g., 'AmazonEC2')", required=True),
    ],
)

cost_get_cost_by_service = AWSCliTool(
    name="cost_get_cost_by_service",
    description="Get AWS costs broken down by service",
    content="""aws ce get-cost-and-usage \
        --time-period Start=$(python3 -c "from datetime import datetime, timedelta; print((datetime.now() - timedelta(days=int('$time_ago'.replace('d', '')))).strftime('%Y-%m-%d'))"),End=$(date +%Y-%m-%d) \
        --granularity MONTHLY \
        --metrics UnblendedCost \
        --group-by Type=DIMENSION,Key=SERVICE""",
    args=[
        Arg(name="time_ago", type="str", description="Time period to analyze (e.g., '30d' for last 30 days)", required=True),
    ],
    mermaid_diagram="""
    graph TD
        A[👤 User] -->|Request: Cost by service| B[🤖 TeamMate]
        B --> C{{"Time period?" ⏰}}
        C --> D[User provides period ✍️]
        D --> E[API request to AWS ☁️]
        E --> F[AWS retrieves cost data 💰]
        F --> G[Group by service 📊]

        style A fill:#f0f9ff,stroke:#0369a1,stroke-width:2px;
        style B fill:#dbeafe,stroke:#3b82f6,stroke-width:2px;
        style C fill:#d1fae5,stroke:#059669,stroke-width:2px;
        style D fill:#bbf7d0,stroke:#16a34a,stroke-width:2px;
        style E fill:#fee2e2,stroke:#ef4444,stroke-width:2px;
        style F fill:#ffedd5,stroke:#ea580c,stroke-width:2px;
        style G fill:#fef08a,stroke:#ca8a04,stroke-width:2px;
    """
)

cost_get_cost_by_tag = AWSCliTool(
    name="cost_get_cost_by_tag",
    description="Get AWS costs broken down by specific tag",
    content="""aws ce get-cost-and-usage \
        --time-period Start=$(python3 -c "from datetime import datetime, timedelta; print((datetime.now() - timedelta(days=int('$time_ago'.replace('d', '')))).strftime('%Y-%m-%d'))"),End=$(date +%Y-%m-%d) \
        --granularity MONTHLY \
        --metrics UnblendedCost \
        --group-by Type=TAG,Key=$tag_key""",
    args=[
        Arg(name="time_ago", type="str", description="Time period to analyze (e.g., '30d' for last 30 days)", required=True),
        Arg(name="tag_key", type="str", description="Tag key to group costs by (e.g., 'Environment', 'Project')", required=True),
    ],
    mermaid_diagram="""
    graph TD
        A[👤 User] -->|Request: Cost by tag| B[🤖 TeamMate]
        B --> C{{"Time period and tag?" 🏷️}}
        C --> D[User provides details ✍️]
        D --> E[API request to AWS ☁️]
        E --> F[AWS retrieves cost data 💰]
        F --> G[Group by tag value 📊]

        style A fill:#f0f9ff,stroke:#0369a1,stroke-width:2px;
        style B fill:#dbeafe,stroke:#3b82f6,stroke-width:2px;
        style C fill:#d1fae5,stroke:#059669,stroke-width:2px;
        style D fill:#bbf7d0,stroke:#16a34a,stroke-width:2px;
        style E fill:#fee2e2,stroke:#ef4444,stroke-width:2px;
        style F fill:#ffedd5,stroke:#ea580c,stroke-width:2px;
        style G fill:#fef08a,stroke:#ca8a04,stroke-width:2px;
    """
)

cost_get_anomalies = AWSCliTool(
    name="cost_get_anomalies",
    description="Get cost anomalies detected by AWS Cost Explorer",
    content="""aws ce get-anomalies \
        --date-interval Start=$(python3 -c "from datetime import datetime, timedelta; print((datetime.now() - timedelta(days=int('$time_ago'.replace('d', '')))).strftime('%Y-%m-%d'))"),End=$(date +%Y-%m-%d)""",
    args=[
        Arg(name="time_ago", type="str", description="Time period to analyze (e.g., '30d' for last 30 days)", required=True),
    ],
    mermaid_diagram="""
    graph TD
        A[👤 User] -->|Request: Cost anomalies| B[🤖 TeamMate]
        B --> C{{"Time period?" ⏰}}
        C --> D[User provides period ✍️]
        D --> E[API request to AWS ☁️]
        E --> F[AWS analyzes cost patterns 📊]
        F --> G[Identify anomalies ⚠️]

        style A fill:#f0f9ff,stroke:#0369a1,stroke-width:2px;
        style B fill:#dbeafe,stroke:#3b82f6,stroke-width:2px;
        style C fill:#d1fae5,stroke:#059669,stroke-width:2px;
        style D fill:#bbf7d0,stroke:#16a34a,stroke-width:2px;
        style E fill:#fee2e2,stroke:#ef4444,stroke-width:2px;
        style F fill:#ffedd5,stroke:#ea580c,stroke-width:2px;
        style G fill:#fef08a,stroke:#ca8a04,stroke-width:2px;
    """
)

tool_registry.register("aws", cost_get_cost_and_usage)
tool_registry.register("aws", cost_get_cost_forecast)
tool_registry.register("aws", cost_get_reservation_utilization)
tool_registry.register("aws", cost_get_savings_plans_utilization)
tool_registry.register("aws", cost_get_rightsizing_recommendation)
tool_registry.register("aws", cost_get_cost_by_service)
tool_registry.register("aws", cost_get_cost_by_tag)
tool_registry.register("aws", cost_get_anomalies)