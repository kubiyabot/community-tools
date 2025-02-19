from kubiya_sdk.tools import Arg
from kubiya_sdk.tools.registry import tool_registry
from tools.base import BaseCVETool

def format_cve_output(data: dict) -> str:
    """Helper method to format CVE output in a readable format"""
    if "message" in data:
        return data["message"]
    
    output = []
    for result in data.get("results", []):
        if "error" in result:
            output.append(f"CVE {result['cve_id']}: {result['error']}")
        else:
            output.append(
                f"CVE ID: {result['cve_id']}\\n"
                f"Severity: {result['severity']}\\n"
                f"Published: {result['published']}\\n"
                f"Last Modified: {result['lastModified']}\\n"
                f"Description: {result['description']}\\n"
            )
    
    return "\\n".join(output) if output else "No CVEs found"

def format_remediation_output(data: dict) -> str:
    """Helper method to format remediation output in a readable format"""
    if "message" in data:
        return data["message"]
    
    output = []
    for result in data.get("results", []):
        if "error" in result:
            output.append(f"CVE {result['cve_id']}: {result['error']}")
        else:
            remediation_text = (
                f"CVE ID: {result['cve_id']}\\n"
                f"Severity: {result['severity']}\\n"
                f"\\nDescription:\\n{result['description']}\\n"
                f"\\nRemediation Steps:\\n{result['remediation_steps'][0]}\\n"
            )
            
            if result['patch_links']:
                remediation_text += f"\\nPatch Links:\\n" + "\\n".join(result['patch_links']) + "\\n"
            
            if result['vendor_advisories']:
                remediation_text += f"\\nVendor Advisories:\\n" + "\\n".join(result['vendor_advisories']) + "\\n"
            
            output.append(remediation_text)
    
    return "\\n\\n".join(output) if output else "No remediation information found"

cve_info = BaseCVETool(
    name="cve_info",
    description="Get detailed information about specific CVE(s)",
    content="""
# Get CVE IDs from arguments
cve_ids = cve_ids.split(',') if cve_ids else []

class CVELookup(BaseNVDAPI):
    def lookup_cves(self, cve_ids: List[str]) -> Dict:
        if not cve_ids:
            return {"message": "No CVE IDs provided"}

        results = []
        for cve_id in cve_ids:
            try:
                data = self.make_request({'cveId': cve_id})
                
                if 'error' in data:
                    results.append({
                        'cve_id': cve_id,
                        'error': data['error']
                    })
                    continue
                
                if data['vulnerabilities']:
                    vuln = data['vulnerabilities'][0]['cve']
                    results.append({
                        'cve_id': vuln['id'],
                        'description': vuln['descriptions'][0]['value'],
                        'severity': vuln.get('metrics', {}).get('cvssMetricV31', [{}])[0].get('cvssData', {}).get('baseScore', 'N/A'),
                        'published': vuln['published'],
                        'lastModified': vuln['lastModified']
                    })
                else:
                    results.append({
                        'cve_id': cve_id,
                        'error': 'CVE not found'
                    })
            except Exception as e:
                results.append({
                    'cve_id': cve_id,
                    'error': str(e)
                })

        if not results:
            return {"message": "No CVEs found"}
        
        return {"results": results}

# Initialize lookup and get results
lookup = CVELookup()
results = lookup.lookup_cves(cve_ids)

print(format_cve_output(results))
""",
    args=[
        Arg(
            name="cve_ids",
            type="str",
            description="Comma-separated list of CVE IDs (e.g., 'CVE-2021-44228,CVE-2022-22965')",
            required=True
        ),
    ],
)

cve_remediation = BaseCVETool(
    name="cve_remediation_steps",
    description="Get remediation steps and recommendations for specific CVE(s)",
    content="""
# Get CVE IDs from arguments
cve_ids = cve_ids.split(',') if cve_ids else []

class CVERemediation(BaseNVDAPI):
    def get_remediation_steps(self, cve_ids: List[str]) -> Dict:
        if not cve_ids:
            return {"message": "No CVE IDs provided"}

        results = []
        for cve_id in cve_ids:
            try:
                data = self.make_request({'cveId': cve_id})
                
                if 'error' in data:
                    results.append({
                        'cve_id': cve_id,
                        'error': data['error']
                    })
                    continue

                if not data['vulnerabilities']:
                    results.append({
                        'cve_id': cve_id,
                        'error': 'CVE not found'
                    })
                    continue

                vuln = data['vulnerabilities'][0]['cve']
                references = vuln.get('references', [])
                
                remediation_info = {
                    'cve_id': vuln['id'],
                    'severity': vuln.get('metrics', {}).get('cvssMetricV31', [{}])[0].get('cvssData', {}).get('baseScore', 'N/A'),
                    'description': vuln['descriptions'][0]['value'],
                    'remediation_steps': [],
                    'vendor_advisories': [],
                    'patch_links': [],
                }

                # Analyze references for remediation information
                for ref in references:
                    ref_url = ref.get('url', '')
                    tags = ref.get('tags', [])
                    
                    if 'Patch' in tags or 'Update' in tags:
                        remediation_info['patch_links'].append(ref_url)
                    elif 'Vendor Advisory' in tags:
                        remediation_info['vendor_advisories'].append(ref_url)

                # Generate basic remediation steps based on vulnerability type
                desc_lower = remediation_info['description'].lower()
                if 'sql injection' in desc_lower:
                    remediation_info['remediation_steps'].append(
                        "1. Implement input validation and parameterized queries\\n"
                        "2. Use an ORM or prepared statements\\n"
                        "3. Apply principle of least privilege to database users\\n"
                        "4. Regular security audits of SQL queries"
                    )
                elif 'buffer overflow' in desc_lower:
                    remediation_info['remediation_steps'].append(
                        "1. Update to the latest version that patches this vulnerability\\n"
                        "2. Enable address space layout randomization (ASLR)\\n"
                        "3. Use languages/frameworks with built-in memory safety\\n"
                        "4. Implement bounds checking"
                    )
                elif 'cross-site scripting' in desc_lower or 'xss' in desc_lower:
                    remediation_info['remediation_steps'].append(
                        "1. Implement proper output encoding\\n"
                        "2. Use Content Security Policy (CSP) headers\\n"
                        "3. Validate and sanitize all user inputs\\n"
                        "4. Use modern frameworks with built-in XSS protection"
                    )

                # Default remediation steps if no specific type is identified
                if not remediation_info['remediation_steps']:
                    remediation_info['remediation_steps'].append(
                        "1. Update affected software to the latest version\\n"
                        "2. Apply security patches as soon as available\\n"
                        "3. Monitor vendor advisories for updates\\n"
                        "4. Implement defense-in-depth security measures"
                    )

                results.append(remediation_info)

            except Exception as e:
                results.append({
                    'cve_id': cve_id,
                    'error': str(e)
                })

        if not results:
            return {"message": "No remediation information found"}
        
        return {"results": results}

# Initialize remediation lookup and get results
remediation = CVERemediation()
results = remediation.get_remediation_steps(cve_ids)

print(format_remediation_output(results))
""",
    args=[
        Arg(
            name="cve_ids",
            type="str",
            description="Comma-separated list of CVE IDs (e.g., 'CVE-2021-44228,CVE-2022-22965')",
            required=True
        ),
    ],
)

# Collect all CVE tools in a list
cve_tools = [
    cve_info,
    cve_remediation,
]

# Register all CVE tools
for tool in cve_tools:
    tool_registry.register("cve", tool) 