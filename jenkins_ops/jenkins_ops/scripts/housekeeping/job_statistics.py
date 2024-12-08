#!/usr/bin/env python3
import os
import sys
import logging
import requests
import json
from typing import Dict, Any, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class JenkinsJobAnalyzer:
    def __init__(self, jenkins_url: str, auth: tuple):
        self.jenkins_url = jenkins_url.rstrip('/')
        self.session = requests.Session()
        self.session.auth = auth
        self.session.headers.update({'Content-Type': 'application/json'})

    def get_job_stats(self, job_name: str, days: int = 30) -> Dict[str, Any]:
        """Get statistics for a specific job."""
        try:
            url = f"{self.jenkins_url}/job/{job_name}/api/json?tree=builds[number,timestamp,duration,result,building]"
            response = self.session.get(url)
            response.raise_for_status()
            builds = response.json().get('builds', [])

            # Calculate cutoff time
            cutoff_time = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)

            # Filter and analyze builds
            recent_builds = [b for b in builds if b['timestamp'] > cutoff_time]
            
            if not recent_builds:
                return {
                    "success": True,
                    "message": f"No builds found in the last {days} days",
                    "stats": None
                }

            # Calculate statistics
            total_builds = len(recent_builds)
            successful_builds = sum(1 for b in recent_builds if b['result'] == 'SUCCESS')
            failed_builds = sum(1 for b in recent_builds if b['result'] == 'FAILURE')
            running_builds = sum(1 for b in recent_builds if b['building'])
            
            durations = [b['duration'] for b in recent_builds if b['duration'] > 0]
            avg_duration = sum(durations) / len(durations) if durations else 0

            return {
                "success": True,
                "stats": {
                    "period_days": days,
                    "total_builds": total_builds,
                    "successful_builds": successful_builds,
                    "failed_builds": failed_builds,
                    "running_builds": running_builds,
                    "success_rate": (successful_builds / total_builds * 100) if total_builds > 0 else 0,
                    "average_duration_ms": avg_duration,
                    "average_duration_readable": str(timedelta(milliseconds=avg_duration)),
                    "builds_per_day": total_builds / days
                }
            }
        except Exception as e:
            logger.error(f"Failed to get job statistics: {str(e)}")
            return {"success": False, "message": str(e)}

    def get_all_jobs_summary(self) -> Dict[str, Any]:
        """Get summary statistics for all jobs."""
        try:
            url = f"{self.jenkins_url}/api/json?tree=jobs[name,color,lastBuild[timestamp,duration,result]]"
            response = self.session.get(url)
            response.raise_for_status()
            jobs = response.json().get('jobs', [])

            job_summaries = []
            for job in jobs:
                last_build = job.get('lastBuild', {})
                job_summaries.append({
                    "name": job['name'],
                    "status": job['color'],
                    "last_build": {
                        "timestamp": last_build.get('timestamp'),
                        "duration": last_build.get('duration'),
                        "result": last_build.get('result')
                    }
                })

            return {
                "success": True,
                "summary": {
                    "total_jobs": len(jobs),
                    "active_jobs": sum(1 for j in jobs if j['color'] != 'disabled'),
                    "jobs": job_summaries
                }
            }
        except Exception as e:
            logger.error(f"Failed to get jobs summary: {str(e)}")
            return {"success": False, "message": str(e)}

def main():
    logging.basicConfig(level=logging.INFO)

    jenkins_url = os.environ.get('JENKINS_URL')
    username = os.environ.get('JENKINS_USERNAME')
    api_token = os.environ.get('JENKINS_API_TOKEN')
    action = os.environ.get('ACTION', 'summary')
    job_name = os.environ.get('JOB_NAME')
    days = int(os.environ.get('DAYS', '30'))

    if not all([jenkins_url, username, api_token]):
        logger.error("Missing required environment variables")
        sys.exit(1)

    analyzer = JenkinsJobAnalyzer(jenkins_url, auth=(username, api_token))

    if action == "summary":
        result = analyzer.get_all_jobs_summary()
    elif action == "job_stats":
        if not job_name:
            result = {
                "success": False,
                "message": "JOB_NAME required for job_stats action"
            }
        else:
            result = analyzer.get_job_stats(job_name, days)
    else:
        result = {"success": False, "message": f"Unknown action: {action}"}

    print(json.dumps(result, indent=2))
    sys.exit(0 if result['success'] else 1)

if __name__ == '__main__':
    main() 