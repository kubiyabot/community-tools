from ..tools.base import AwsBaseTool, LoggingArgsMixin, MetricsArgsMixin
from kubiya_sdk.tools import Arg
from kubiya_sdk.tools.registry import tool_registry

class CloudWatchLogTool(AwsBaseTool, LoggingArgsMixin):
    """AWS CloudWatch tool with logging capabilities."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_common_log_args()

class CloudWatchMetricTool(AwsBaseTool, MetricsArgsMixin):
    """AWS CloudWatch tool with metrics capabilities."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_common_metric_args()

class CloudWatchTools:
    """AWS CloudWatch monitoring and logging tools."""
    
    def __init__(self):
        """Initialize and register all CloudWatch tools."""
        tools = [
            self.get_log_events(),
            self.get_metrics(),
            self.describe_alarms(),
            self.get_metric_statistics()
        ]
        
        for tool in tools:
            tool_registry.register("cloudwatch", tool)

    def get_log_events(self) -> CloudWatchLogTool:
        """Get log events from CloudWatch Logs."""
        return CloudWatchLogTool(
            name="get_log_events",
            description="Get log events from CloudWatch Logs",
            content="""
            if [ -z "$log_group" ] || [ -z "$log_stream" ]; then
                echo "Error: Log group and stream names are required"
                exit 1
            fi

            PARAMS="--log-group-name $log_group --log-stream-name $log_stream"
            if [ ! -z "$start_time" ]; then
                PARAMS="$PARAMS --start-time $start_time"
            fi
            if [ ! -z "$end_time" ]; then
                PARAMS="$PARAMS --end-time $end_time"
            fi
            if [ ! -z "$limit" ]; then
                PARAMS="$PARAMS --limit $limit"
            fi

            aws logs get-log-events $PARAMS
            """,
            args=[
                Arg(name="log_group",
                    description="CloudWatch Log Group name",
                    required=True),
                Arg(name="log_stream",
                    description="CloudWatch Log Stream name",
                    required=True)
            ]
        )

    def get_metrics(self) -> CloudWatchMetricTool:
        """Get CloudWatch metrics data."""
        return CloudWatchMetricTool(
            name="get_metrics",
            description="Get CloudWatch metrics data for the past hour.",
            content="""
            if [ -z "$metric_name" ] || [ -z "$namespace" ]; then
                echo "Error: Metric name and namespace are required"
                exit 1
            fi

            START_TIME=$(date -u -d '-1 hour' +%Y-%m-%dT%H:%M:%SZ)
            END_TIME=$(date -u +%Y-%m-%dT%H:%M:%SZ)

            aws cloudwatch get-metric-data \
                --metric-data-queries "[{
                    \\"Id\\": \\"m1\\",
                    \\"MetricStat\\": {
                        \\"Metric\\": {
                            \\"Namespace\\": \\"$namespace\\",
                            \\"MetricName\\": \\"$metric_name\\"
                        },
                        \\"Period\\": 300,
                        \\"Stat\\": \\"Average\\"
                    }
                }]" \
                --start-time "$START_TIME" \
                --end-time "$END_TIME"
            """,
            args=[
                Arg(
                    name="namespace",
                    description="CloudWatch metrics namespace",
                    required=True
                ),
                Arg(
                    name="metric_name",
                    description="Name of the metric to retrieve",
                    required=True
                )
            ]
        )

    def describe_alarms(self) -> AwsBaseTool:
        """Describe CloudWatch alarms."""
        return AwsBaseTool(
            name="describe_alarms",
            description="Get details about CloudWatch alarms",
            content="""
            PARAMS=""
            if [ ! -z "$alarm_names" ]; then
                PARAMS="--alarm-names $alarm_names"
            fi
            if [ ! -z "$state" ]; then
                PARAMS="$PARAMS --state-value $state"
            fi

            aws cloudwatch describe-alarms $PARAMS
            """,
            args=[
                Arg(name="alarm_names",
                    description="Comma-separated list of alarm names",
                    required=False),
                Arg(name="state",
                    description="Filter by alarm state",
                    required=False)
            ]
        )

    def get_metric_statistics(self) -> CloudWatchMetricTool:
        """Get detailed statistics for a metric."""
        return CloudWatchMetricTool(
            name="get_metric_statistics",
            description="Get detailed statistics for a CloudWatch metric",
            content="""
            if [ -z "$metric_name" ] || [ -z "$namespace" ]; then
                echo "Error: Metric name and namespace are required"
                exit 1
            fi

            aws cloudwatch get-metric-statistics \
                --namespace "$namespace" \
                --metric-name "$metric_name" \
                --dimensions Name=ServiceName,Value=${service_name:-*} \
                --start-time "$start_time" \
                --end-time "$end_time" \
                --period ${period:-300} \
                --statistics ${statistics:-Average}
            """,
            args=[
                Arg(name="namespace",
                    description="CloudWatch metrics namespace",
                    required=True),
                Arg(name="service_name",
                    description="Name of the service",
                    required=False)
            ]
        )

# Initialize when module is imported
CloudWatchTools() 