from kubiya_sdk.tools import Arg
from kubiya_sdk.tools.registry import tool_registry
from ..base import PythonTool

summarize_observability_findings = PythonTool(
    name="summarize_observability_findings",
    description="Summarize observability data (metrics, logs, traces) and recommend a Slack channel",
    content="""
import json

# Parse inputs
metrics = json.loads(cloudwatch_metrics)
logs = json.loads(log_findings)
traces = json.loads(trace_findings)
alert = alert_context

summary = []
recommended_channel = "#platform-team"  # default

# Analyze metrics
queue_depth = metrics.get("ApproximateNumberOfMessages", {}).get("Datapoints", [])
queue_age = metrics.get("ApproximateAgeOfOldestMessage", {}).get("Datapoints", [])
cpu = metrics.get("CPUUtilization", {}).get("Datapoints", [])

if queue_depth:
    max_depth = max([p.get("Average", 0) for p in queue_depth])
    summary.append(f"📦 Queue depth peaked at {int(max_depth)} messages.")

if queue_age:
    max_age = max([p.get("Average", 0) for p in queue_age])
    summary.append(f"⏳ Oldest message was in the queue for ~{int(max_age)} seconds.")

if cpu:
    avg_cpu = sum([p.get("Average", 0) for p in cpu]) / len(cpu)
    summary.append(f"🧠 ECS CPU utilization averaged {round(avg_cpu, 1)}%.")

# Analyze logs
log_lines = logs.get("lines", [])
error_lines = [line for line in log_lines if "ERROR" in line.upper()]

if error_lines:
    summary.append(f"🚨 Found {len(error_lines)} error log(s). Sample: `{error_lines[0][:100]}`")
    recommended_channel = "#engineering"

# Analyze traces
trace_data = traces.get("results", [])
p99 = None
for item in trace_data:
    if item.get("op") == "P99":
        p99 = item.get("value")
if p99:
    summary.append(f"📈 P99 latency: {int(p99)}ms")

# Detect abuse pattern (fake: assume any log line with user_id is suspicious)
user_id_hits = [line for line in log_lines if "user_id" in line]
if len(user_id_hits) > 5:
    summary.append("⚠️ Potential abuse pattern detected from a specific client (based on logs).")
    recommended_channel = "#customer-success"

# Output final result
result = {
    "summary": "\n".join(summary),
    "recommended_channel": recommended_channel
}
print(json.dumps(result, indent=2))
    """,
    args=[
        Arg(name="cloudwatch_metrics", type="str", description="Raw JSON output from metric tool", required=True),
        Arg(name="log_findings", type="str", description="Raw JSON from log search", required=True),
        Arg(name="trace_findings", type="str", description="Raw JSON from Honeycomb trace tool", required=True),
        Arg(name="alert_context", type="dict", description="The full alert object", required=True),
    ]
)

tool_registry.register("diagnostics", summarize_observability_findings)
