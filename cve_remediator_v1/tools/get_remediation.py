import requests
from typing import List

def get_remediation_info(cve_ids: List[str]) -> dict:
    # Using OSV (Open Source Vulnerabilities) database direct vulnerability lookup
    OSV_API_URL = "https://api.osv.dev/v1/vulns"
    
    results = {}
    for cve_id in cve_ids:
        try:
            # Direct vulnerability lookup
            response = requests.get(f"{OSV_API_URL}/{cve_id}")
            response.raise_for_status()
            vuln = response.json()
            
            results[cve_id] = {
                'affected_versions': [affected.get('package', {}).get('name') for affected in vuln.get('affected', [])],
                'fixed_versions': [],
                'recommendations': []
            }
            
            # Extract fixed versions and recommendations
            for affected in vuln.get('affected', []):
                for ranges in affected.get('ranges', []):
                    if ranges.get('type') == 'GIT':
                        for event in ranges.get('events', []):
                            if event.get('fixed'):
                                results[cve_id]['fixed_versions'].append(event.get('fixed'))
                
                if affected.get('database_specific', {}).get('solution'):
                    results[cve_id]['recommendations'].append(
                        affected['database_specific']['solution']
                    )
            
        except Exception as e:
            results[cve_id] = {
                'error': f"Failed to fetch remediation data: {str(e)}"
            }
    
    return results

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Get CVE Remediation Information")
    parser.add_argument("cve_ids", help="Comma-separated list of CVE IDs")
    
    args = parser.parse_args()
    cve_list = [cve.strip() for cve in args.cve_ids.split(',')]
    
    try:
        remediation_info = get_remediation_info(cve_list)
        
        print("\nRemediation Information:")
        for cve_id, info in remediation_info.items():
            print(f"\n{cve_id}:")
            if 'error' in info:
                print(f"Error: {info['error']}")
                continue
                
            if info['affected_versions']:
                print("Affected Packages:")
                for pkg in info['affected_versions']:
                    print(f"- {pkg}")
                    
            if info['fixed_versions']:
                print("\nFixed in versions:")
                for version in info['fixed_versions']:
                    print(f"- {version}")
                    
            if info['recommendations']:
                print("\nRecommendations:")
                for rec in info['recommendations']:
                    print(f"- {rec}")
            
    except Exception as e:
        print(f"Error: {str(e)}")
        raise RuntimeError(str(e))

if __name__ == "__main__":
    main() 