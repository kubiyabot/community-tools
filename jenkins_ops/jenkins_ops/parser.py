import logging
import json
from typing import Dict, Any, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from urllib.parse import urljoin
import base64

logger = logging.getLogger(__name__)

class JenkinsJobParser:
    """Parser for Jenkins jobs using direct HTTP requests and JSON API."""
    
    def __init__(
        self,
        jenkins_url: str,
        username: str,
        api_token: str,
        max_workers: int = 4
    ):
        self.jenkins_url = jenkins_url.rstrip('/')
        self.username = username
        self.api_token = api_token
        self.max_workers = max_workers
        self.warnings = []
        self.errors = []
        self.session = self._create_session()

    def _get_all_jobs_recursive(self, url: str = None) -> List[Dict[str, str]]:
        """Recursively get all jobs from Jenkins, including those in folders."""
        try:
            if url is None:
                url = f"{self.jenkins_url}/api/json"

            response = self._make_request(url)
            if not response:
                return []

            jobs = []
            for item in response.get('jobs', []):
                item_class = item.get('_class', '')
                
                # Handle different job types
                if 'WorkflowJob' in item_class or 'FreeStyleProject' in item_class:
                    # Regular job
                    jobs.append({
                        'name': item['name'],
                        'full_name': item['fullName'] if 'fullName' in item else item['name'],
                        'url': item['url']
                    })
                elif 'Folder' in item_class or 'WorkflowMultiBranchProject' in item_class:
                    # Folder or Multibranch Pipeline - recurse into it
                    sub_jobs = self._get_all_jobs_recursive(f"{item['url']}api/json")
                    jobs.extend(sub_jobs)

            return jobs

        except Exception as e:
            error_msg = f"Failed to get jobs from {url}: {str(e)}"
            logger.error(error_msg)
            self.errors.append(error_msg)
            return []

    def get_jobs(self, job_filter: Optional[List[str]] = None) -> Tuple[Dict[str, Any], List[str], List[str]]:
        """Get all Jenkins jobs and their parameters."""
        jobs_info = {}
        
        try:
            # Get all jobs recursively
            logger.info("Starting Jenkins job discovery...")
            all_jobs = self._get_all_jobs_recursive()
            logger.info(f"Found {len(all_jobs)} total jobs")
            
            # Filter jobs if needed
            jobs_to_process = [
                job for job in all_jobs
                if not job_filter or job['full_name'] in job_filter
            ]
            
            logger.info(f"Processing {len(jobs_to_process)} jobs after filtering")

            if not jobs_to_process:
                self.warnings.append("No matching jobs found")
                return {}, self.warnings, self.errors

            # Process jobs in parallel
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_job = {
                    executor.submit(
                        self._process_single_job,
                        job['full_name']
                    ): job
                    for job in jobs_to_process
                }

                for future in as_completed(future_to_job):
                    job = future_to_job[future]
                    try:
                        job_info = future.result()
                        if job_info:
                            jobs_info[job['full_name']] = job_info
                            logger.info(f"Successfully processed job: {job['full_name']}")
                    except Exception as e:
                        error_msg = f"Failed to process job {job['full_name']}: {str(e)}"
                        logger.error(error_msg)
                        self.errors.append(error_msg)

        except Exception as e:
            error_msg = f"Failed to get jobs: {str(e)}"
            logger.error(error_msg)
            self.errors.append(error_msg)

        if not jobs_info and not self.errors:
            self.errors.append("No jobs were found or all jobs failed to process")

        logger.info(f"Completed job discovery. Found {len(jobs_info)} valid jobs")
        return jobs_info, self.warnings, self.errors

    # ... (rest of the existing methods remain the same)