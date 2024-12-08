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

    def _create_session(self) -> requests.Session:
        """Create and configure requests session with authentication."""
        session = requests.Session()
        auth = base64.b64encode(f"{self.username}:{self.api_token}".encode()).decode()
        session.headers.update({
            'Authorization': f'Basic {auth}',
            'Content-Type': 'application/json',
        })
        return session

    def _make_request(self, endpoint: str, method: str = 'GET', **kwargs) -> Optional[Dict[str, Any]]:
        """Make HTTP request to Jenkins API."""
        url = endpoint if endpoint.startswith('http') else urljoin(self.jenkins_url, endpoint.lstrip('/'))
        try:
            response = self.session.request(
                method=method,
                url=url,
                **kwargs
            )
            response.raise_for_status()
            return response.json() if response.content else None
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for {url}: {str(e)}")
            self.errors.append(f"API request failed: {str(e)}")
            return None

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

    def _process_single_job(self, job_name: str) -> Optional[Dict[str, Any]]:
        """Process a single Jenkins job."""
        try:
            # Get job info with parameters using JSON API
            info_endpoint = f'job/{job_name}/api/json?tree=description,url,buildable,property[*],lastBuild[*],lastSuccessfulBuild[*],healthReport[*]'
            job_info = self._make_request(info_endpoint)
            
            if not job_info:
                raise Exception("Failed to get job information")

            # Extract parameters from job properties
            parameters = self._extract_parameters_from_properties(job_info.get('property', []))
            
            # Get additional job information
            last_build = job_info.get('lastBuild', {})
            last_successful_build = job_info.get('lastSuccessfulBuild', {})
            
            # Get detailed build information if available
            if last_build:
                last_build = self._make_request(f"{last_build['url']}api/json")
            if last_successful_build:
                last_successful_build = self._make_request(f"{last_successful_build['url']}api/json")
            
            return {
                "name": job_name,
                "description": job_info.get('description', ''),
                "parameters": parameters,
                "url": job_info.get('url', ''),
                "buildable": job_info.get('buildable', True),
                "type": self._determine_job_type(job_info),
                "last_build": {
                    "number": last_build.get('number'),
                    "url": last_build.get('url'),
                    "timestamp": last_build.get('timestamp'),
                    "duration": last_build.get('duration'),
                    "result": last_build.get('result')
                } if last_build else None,
                "last_successful_build": {
                    "number": last_successful_build.get('number'),
                    "url": last_successful_build.get('url'),
                    "timestamp": last_successful_build.get('timestamp'),
                    "duration": last_successful_build.get('duration')
                } if last_successful_build else None,
                "health": self._get_job_health(job_info),
                "auth": {
                    "username": self.username
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to process job {job_name}: {str(e)}")
            return None

    def _extract_parameters_from_properties(self, properties: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract parameters from job properties."""
        parameters = {}
        
        for prop in properties:
            if 'parameterDefinitions' in prop:
                for param in prop['parameterDefinitions']:
                    param_type = param.get('_class', '').split('.')[-1]
                    param_name = param.get('name', '')
                    
                    param_config = {
                        "type": "str",  # All parameters are strings in Kubiya
                        "description": param.get('description', ''),
                        "required": True,  # Jenkins parameters are typically required
                        "default": param.get('defaultValue')
                    }
                    
                    # Add choices if available
                    if 'choices' in param:
                        param_config['choices'] = param['choices']
                    
                    parameters[param_name] = param_config
        
        return parameters

    def _determine_job_type(self, job_info: Dict[str, Any]) -> str:
        """Determine the type of Jenkins job."""
        job_class = job_info.get('_class', '')
        
        if 'WorkflowJob' in job_class:
            return 'pipeline'
        elif 'FreeStyleProject' in job_class:
            return 'freestyle'
        elif 'WorkflowMultiBranchProject' in job_class:
            return 'multibranch-pipeline'
        else:
            return 'unknown'

    def _get_job_health(self, job_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get job health information."""
        try:
            health_report = job_info.get('healthReport', [])
            if health_report:
                return {
                    "score": health_report[0].get('score', 0),
                    "description": health_report[0].get('description', '')
                }
            return None
        except Exception:
            return None

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