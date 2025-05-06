from kubiya_sdk.tools import Arg
from .base import AWSCliTool, AWSSdkTool
from kubiya_sdk.tools.registry import tool_registry

cloudwatch_list_metrics = AWSCliTool(
    name="cloudwatch_list_metrics",
    description="List CloudWatch metrics",
    content="aws cloudwatch list-metrics $([[ -n \"$namespace\" ]] && echo \"--namespace $namespace\") $([[ -n \"$metric_name\" ]] && echo \"--metric-name $metric_name\")",
    args=[
        Arg(name="namespace", type="str", description="Metric namespace (e.g., 'AWS/EC2')", required=False),
        Arg(name="metric_name", type="str", description="Metric name (e.g., 'CPUUtilization')", required=False),
    ],
    mermaid_diagram="""
    graph TD
        A[👤 User] -->|Request: List metrics| B[🤖 TeamMate]
        B --> C{{"Namespace/metric name (optional)?" 🔢}}
        C --> D[User provides details ✍️]
        D --> E[API request to AWS ☁️]
        E --> F[AWS retrieves metrics 📊]
        F --> G[User receives metric list 📄]

        style A fill:#f0f9ff,stroke:#0369a1,stroke-width:2px;
        style B fill:#dbeafe,stroke:#3b82f6,stroke-width:2px;
        style C fill:#d1fae5,stroke:#059669,stroke-width:2px;
        style D fill:#bbf7d0,stroke:#16a34a,stroke-width:2px;
        style E fill:#fee2e2,stroke:#ef4444,stroke-width:2px;
        style F fill:#ffedd5,stroke:#ea580c,stroke-width:2px;
        style G fill:#e0f2fe,stroke:#0284c7,stroke-width:2px;
    """
)

cloudwatch_put_metric_alarm = AWSCliTool(
    name="cloudwatch_put_metric_alarm",
    description="Create or update a CloudWatch alarm",
    content="aws cloudwatch put-metric-alarm --alarm-name $alarm_name --metric-name $metric_name --namespace $namespace --statistic $statistic --period $period --threshold $threshold --comparison-operator $comparison_operator --evaluation-periods $evaluation_periods",
    args=[
        Arg(name="alarm_name", type="str", description="Name for the alarm", required=True),
        Arg(name="metric_name", type="str", description="Name of the metric", required=True),
        Arg(name="namespace", type="str", description="Namespace of the metric", required=True),
        Arg(name="statistic", type="str", description="Statistic to use (e.g., 'Average', 'Maximum')", required=True),
        Arg(name="period", type="int", description="Period in seconds", required=True),
        Arg(name="threshold", type="float", description="Threshold value", required=True),
        Arg(name="comparison_operator", type="str", description="Comparison operator (e.g., 'GreaterThanThreshold')", required=True),
        Arg(name="evaluation_periods", type="int", description="Number of evaluation periods", required=True),
    ],
    mermaid_diagram="""
    graph TD
        A[👤 User] -->|Request: Create alarm| B[🤖 TeamMate]
        B --> C{{"Alarm details?" 🔢}}
        C --> D[User provides details ✍️]
        D --> E[API request to AWS ☁️]
        E --> F[AWS creates alarm 🚨]
        F --> G[User receives confirmation 📄]

        style A fill:#f0f9ff,stroke:#0369a1,stroke-width:2px;
        style B fill:#dbeafe,stroke:#3b82f6,stroke-width:2px;
        style C fill:#d1fae5,stroke:#059669,stroke-width:2px;
        style D fill:#bbf7d0,stroke:#16a34a,stroke-width:2px;
        style E fill:#fee2e2,stroke:#ef4444,stroke-width:2px;
        style F fill:#ffedd5,stroke:#ea580c,stroke-width:2px;
        style G fill:#e0f2fe,stroke:#0284c7,stroke-width:2px;
    """
)

cloudwatch_describe_alarms = AWSCliTool(
    name="cloudwatch_describe_alarms",
    description="Describe CloudWatch alarms",
    content="aws cloudwatch describe-alarms $([[ -n \"$alarm_names\" ]] && echo \"--alarm-names $alarm_names\")",
    args=[
        Arg(name="alarm_names", type="str", description="Comma-separated list of alarm names (optional)", required=False),
    ],
    mermaid_diagram="""
    graph TD
        A[👤 User] -->|Request: Describe alarms| B[🤖 TeamMate]
        B --> C{{"Alarm names (optional)?" 🔢}}
        C --> D[User provides alarm names ✍️]
        D --> E[API request to AWS ☁️]
        E --> F[AWS retrieves alarm details 📊]
        F --> G[User receives alarm information 📄]

        style A fill:#f0f9ff,stroke:#0369a1,stroke-width:2px;
        style B fill:#dbeafe,stroke:#3b82f6,stroke-width:2px;
        style C fill:#d1fae5,stroke:#059669,stroke-width:2px;
        style D fill:#bbf7d0,stroke:#16a34a,stroke-width:2px;
        style E fill:#fee2e2,stroke:#ef4444,stroke-width:2px;
        style F fill:#ffedd5,stroke:#ea580c,stroke-width:2px;
        style G fill:#e0f2fe,stroke:#0284c7,stroke-width:2px;
    """
)

cloudwatch_delete_alarms = AWSCliTool(
    name="cloudwatch_delete_alarms",
    description="Delete CloudWatch alarms",
    content="aws cloudwatch delete-alarms --alarm-names $alarm_names",
    args=[
        Arg(name="alarm_names", type="str", description="Comma-separated list of alarm names", required=True),
    ],
    mermaid_diagram="""
    graph TD
        A[👤 User] -->|Request: Delete alarms| B[🤖 TeamMate]
        B --> C{{"Alarm names?" 🔢}}
        C --> D[User provides alarm names ✍️]
        D --> E[API request to AWS ☁️]
        E --> F[AWS deletes alarms 🗑️]
        F --> G[User receives confirmation 📄]

        style A fill:#f0f9ff,stroke:#0369a1,stroke-width:2px;
        style B fill:#dbeafe,stroke:#3b82f6,stroke-width:2px;
        style C fill:#d1fae5,stroke:#059669,stroke-width:2px;
        style D fill:#bbf7d0,stroke:#16a34a,stroke-width:2px;
        style E fill:#fee2e2,stroke:#ef4444,stroke-width:2px;
        style F fill:#ffedd5,stroke:#ea580c,stroke-width:2px;
        style G fill:#e0f2fe,stroke:#0284c7,stroke-width:2px;
    """
)

cloudwatch_list_dashboards = AWSCliTool(
    name="cloudwatch_list_dashboards",
    description="List CloudWatch dashboards",
    content="aws cloudwatch list-dashboards",
    args=[],
    mermaid_diagram="""
    graph TD
        A[👤 User] -->|Request: List dashboards| B[🤖 TeamMate]
        B --> C[API request to AWS ☁️]
        C --> D[AWS retrieves dashboard list 📊]
        D --> E[User receives dashboard details 📄]

        style A fill:#f0f9ff,stroke:#0369a1,stroke-width:2px;
        style B fill:#dbeafe,stroke:#3b82f6,stroke-width:2px;
        style C fill:#fee2e2,stroke:#ef4444,stroke-width:2px;
        style D fill:#ffedd5,stroke:#ea580c,stroke-width:2px;
        style E fill:#e0f2fe,stroke:#0284c7,stroke-width:2px;
    """
)

tool_registry.register("aws", cloudwatch_list_metrics)
tool_registry.register("aws", cloudwatch_put_metric_alarm)
tool_registry.register("aws", cloudwatch_describe_alarms)
tool_registry.register("aws", cloudwatch_delete_alarms)
tool_registry.register("aws", cloudwatch_list_dashboards) 