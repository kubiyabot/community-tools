import inspect
from kubiya_sdk.tools import Arg
from ..base import HoneycombTool
from kubiya_sdk.tools.registry import tool_registry
from . import trace_analysis

analyze_traces = HoneycombTool(
    name="analyze_traces",
    description="Query Honeycomb for trace stats like P99 and error rate for a given service",
    content="""python /tmp/trace_analysis.py "{{ .dataset }}" "{{ .service_name }}" "{{ .start_time }}" """,
    args=[
        Arg(name="dataset", type="str", description="Honeycomb dataset name (e.g. 'test')", required=True),
        Arg(name="service_name", type="str", description="The name of the service to analyze", required=True),
        Arg(name="start_time", type="int", description="Minutes to look back from now (e.g. 30)", required=True)
    ],
    with_files=[
        FileSpec(
            destination="/tmp/trace_analysis.py",
            content=inspect.getsource(trace_analysis)
        )
    ]
)

tool_registry.register("honeycomb", analyze_traces)
