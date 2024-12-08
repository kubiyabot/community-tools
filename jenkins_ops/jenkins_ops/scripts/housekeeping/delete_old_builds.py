#!/usr/bin/env python3
import os
import sys
import logging
import time
import requests
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

def delete_old_builds(jenkins_url: str, job_name: str, days: int, auth: tuple) -> Dict[str, Any]:
    """Delete builds older than specified days from a Jenkins job."""
    try:
        # Create session
        session = requests.Session()
        session.auth = auth
        session.headers.update({'Content-Type': 'application/json'})

        # Fetch build information
        url = f"{jenkins_url}/job/{job_name}/api/json?tree=builds[number,timestamp]"
        response = session.get(url)
        response.raise_for_status()
        builds = response.json().get('builds', [])

        # Calculate cutoff timestamp
        cutoff_timestamp = int(time.time() * 1000) - (days * 24 * 60 * 60 * 1000)

        # Delete old builds
        deleted_builds = []
        for build in builds:
            if build['timestamp'] < cutoff_timestamp:
                build_number = build['number']
                delete_url = f"{jenkins_url}/job/{job_name}/{build_number}/doDelete"
                delete_response = session.post(delete_url)
                if delete_response.status_code == 200:
                    logger.info(f"Deleted build #{build_number}")
                    deleted_builds.append(build_number)
                else:
                    logger.error(f"Failed to delete build #{build_number}: {delete_response.text}")

        return {
            "success": True,
            "message": f"Deleted builds: {deleted_builds}" if deleted_builds else "No builds deleted.",
            "deleted_builds": deleted_builds
        }

    except Exception as e:
        logger.error(f"Failed to delete old builds: {str(e)}")
        return {
            "success": False,
            "message": f"Failed to delete old builds: {str(e)}",
            "deleted_builds": []
        }

def main():
    # Configure logging
    logging.basicConfig(level=logging.INFO)

    # Get environment variables
    jenkins_url = os.environ.get('JENKINS_URL')
    username = os.environ.get('JENKINS_USERNAME')
    api_token = os.environ.get('JENKINS_API_TOKEN')
    job_name = os.environ.get('JOB_NAME')
    days = int(os.environ.get('DAYS', '30'))

    # Validate required environment variables
    if not all([jenkins_url, username, api_token, job_name]):
        logger.error("Missing required environment variables")
        sys.exit(1)

    # Execute deletion
    result = delete_old_builds(
        jenkins_url=jenkins_url,
        job_name=job_name,
        days=days,
        auth=(username, api_token)
    )

    # Print result and exit
    print(json.dumps(result, indent=2))
    sys.exit(0 if result['success'] else 1)

if __name__ == '__main__':
    main() 