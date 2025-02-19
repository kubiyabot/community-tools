import inspect
from kubiya_sdk.tools import Arg, FileSpec
from tools.base import CVETool, register_cve_tool
import tools.get_remediation as get_remediation_module
import tools.get_cve_info as get_cve_info_module


cve_info_tool = CVETool(
    name="get_cve_info",
    description="Get detailed information about a specific CVE",
    content="""python /tmp/get_cve_info.py "{{ .cve_id }}" """,
    args=[
        Arg(name="cve_id", description="CVE ID (e.g., CVE-2021-44228)", required=True),
    ],
    with_files=[
        FileSpec(
            destination="/tmp/get_cve_info.py",
            content=inspect.getsource(get_cve_info_module),
        ),
    ]
)

cve_remediation_tool = CVETool(
    name="get_cve_remediation",
    description="Get remediation steps for a list of CVEs",
    content="""python /tmp/get_remediation.py "{{ .cve_ids }}" """,
    args=[
        Arg(name="cve_ids", description="Comma-separated list of CVE IDs", required=True),
    ],
    with_files=[
        FileSpec(
            destination="/tmp/get_remediation.py",
            content=inspect.getsource(get_remediation_module),
        ),
    ]
)

[
    register_cve_tool(tool) for tool in [
        cve_info_tool,
        cve_remediation_tool
    ]
] 