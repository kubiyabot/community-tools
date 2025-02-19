import inspect
from kubiya_sdk.tools import Arg, FileSpec
from base import CVETool, register_cve_tool
from tools import get_remediation

import requests

NVDB_API_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"

def get_cve_info(cve_id: str) -> dict:
    params = {
        "cveId": cve_id
    }
    
    try:
        response = requests.get(NVDB_API_URL, params=params)
        response.raise_for_status()
        data = response.json()
        
        if not data.get('vulnerabilities'):
            print(f"Error: No data found for CVE ID: {cve_id}")
            raise ValueError(f"No data found for CVE ID: {cve_id}")
            
        vuln = data['vulnerabilities'][0]['cve']
        
        return {
            'id': vuln.get('id'),
            'published': vuln.get('published'),
            'lastModified': vuln.get('lastModified'),
            'description': vuln.get('descriptions', [{}])[0].get('value', 'No description available'),
            'metrics': vuln.get('metrics', {}).get('cvssMetricV31', [{}])[0].get('cvssData', {}),
            'references': [ref.get('url') for ref in vuln.get('references', [])]
        }
        
    except requests.exceptions.RequestException as e:
        print(f"Error: Failed to fetch CVE data: {str(e)}")
        raise RuntimeError(f"Failed to fetch CVE data: {str(e)}")
    
    except Exception as e:
        print(f"Error: Failed to fetch CVE data: {str(e)}")
        raise RuntimeError(f"Failed to fetch CVE data: {str(e)}")

cve_info_tool = CVETool(
    name="get_cve_info",
    description="Get detailed information about a specific CVE",
    content="""python /tmp/get_cve_info.py "{{ .cve_id }}" """,
    args=[
        Arg(name="cve_id", type="str", description="CVE ID (e.g., CVE-2021-44228)", required=True),
    ],
    with_files=[
        FileSpec(
            destination="/tmp/get_cve_info.py",
            content=inspect.getsource(get_cve_info),
        ),
    ]
)

cve_remediation_tool = CVETool(
    name="get_cve_remediation",
    description="Get remediation steps for a list of CVEs",
    content="""python /tmp/get_remediation.py "{{ .cve_ids }}" """,
    args=[
        Arg(name="cve_ids", type="str", description="Comma-separated list of CVE IDs", required=True),
    ],
    with_files=[
        FileSpec(
            destination="/tmp/get_remediation.py",
            content=inspect.getsource(get_remediation),
        ),
    ]
)

[
    register_cve_tool(tool) for tool in [
        cve_info_tool,
        cve_remediation_tool
    ]
] 