import logging
import json
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from urllib.parse import urljoin
import base64

logger = logging.getLogger(__name__)

class JenkinsJobParser:
    """Parser for Jenkins jobs using direct HTTP requests."""
    
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
        url = urljoin(self.jenkins_url, endpoint.lstrip('/'))
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
            raise

    def _get_crumb(self) -> Optional[Dict[str, str]]:
        """Get Jenkins CSRF crumb."""
        try:
            response = self._make_request('crumbIssuer/api/json')
            return {
                response.get('crumbRequestField', 'Jenkins-Crumb'): 
                response.get('crumb')
            }
        except Exception:
            return None

    def get_jobs(self, job_filter: Optional[List[str]] = None) -> Tuple[Dict[str, Any], List[str], List[str]]:
        """Get all Jenkins jobs and their parameters."""
        jobs_info = {}
        
        try:
            # Get all jobs recursively
            all_jobs = self._get_all_jobs_recursive()
            
            # Filter jobs if needed
            jobs_to_process = [
                job for job in all_jobs
                if not job_filter or job['full_name'] in job_filter
            ]

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
                    except Exception as e:
                        self.errors.append(f"Failed to process job {job['full_name']}: {str(e)}")

        except Exception as e:
            self.errors.append(f"Failed to get jobs: {str(e)}")

        return jobs_info, self.warnings, self.errors

    def _get_all_jobs_recursive(self, folder_path: str = '') -> List[Dict[str, Any]]:
        """Recursively get all jobs from Jenkins."""
        all_jobs = []
        
        try:
            # Get items at current level
            if folder_path:
                endpoint = f'job/{folder_path}/api/json'
                items = self._make_request(endpoint)['jobs']
            else:
                items = self._make_request('api/json')['jobs']

            for item in items:
                item_class = item.get('_class', '')
                
                # Handle different item types
                if 'WorkflowJob' in item_class:  # Pipeline job
                    all_jobs.append({
                        'name': item['name'],
                        'full_name': f"{folder_path}/{item['name']}" if folder_path else item['name'],
                        'type': 'pipeline',
                        'url': item['url']
                    })
                elif 'FreeStyleProject' in item_class:  # Freestyle job
                    all_jobs.append({
                        'name': item['name'],
                        'full_name': f"{folder_path}/{item['name']}" if folder_path else item['name'],
                        'type': 'freestyle',
                        'url': item['url']
                    })
                elif any(folder_type in item_class for folder_type in ['Folder', 'WorkflowMultiBranchProject']):
                    # Recursively process folders and multibranch pipelines
                    new_path = f"{folder_path}/{item['name']}" if folder_path else item['name']
                    folder_jobs = self._get_all_jobs_recursive(new_path)
                    all_jobs.extend(folder_jobs)
                    
                    # For multibranch pipelines, also get branch jobs
                    if 'WorkflowMultiBranchProject' in item_class:
                        try:
                            endpoint = f'job/{new_path}/api/json'
                            branches = self._make_request(endpoint)['jobs']
                            for branch in branches:
                                all_jobs.append({
                                    'name': f"{item['name']}/{branch['name']}",
                                    'full_name': f"{new_path}/{branch['name']}",
                                    'type': 'multibranch-pipeline',
                                    'url': branch['url']
                                })
                        except Exception as e:
                            self.warnings.append(f"Failed to get branches for {new_path}: {str(e)}")

        except Exception as e:
            self.warnings.append(f"Failed to get jobs from {folder_path}: {str(e)}")

        return all_jobs

    def _process_single_job(self, job_name: str) -> Optional[Dict[str, Any]]:
        """Process a single Jenkins job."""
        try:
            # Get job configuration (XML)
            config_endpoint = f'job/{job_name}/config.xml'
            config_response = self.session.get(urljoin(self.jenkins_url, config_endpoint))
            config_response.raise_for_status()
            job_config = config_response.text
            
            # Parse parameters from config
            parameters = self._parse_job_parameters(job_name, job_config)
            
            # Get job info
            info_endpoint = f'job/{job_name}/api/json'
            job_info = self._make_request(info_endpoint)
            
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

    def _parse_job_parameters(self, job_name: str, job_config: str) -> Dict[str, Any]:
        """Parse parameters from Jenkins job XML configuration."""
        try:
            root = ET.fromstring(job_config)
            parameters = {}
            
            # Find all parameter definitions
            param_paths = [
                ".//hudson.model.ParameterDefinition",  # Standard parameters
                ".//com.cloudbees.plugins.credentials.CredentialsParameterDefinition",  # Credentials
                ".//net.uaznia.lukanus.hudson.plugins.gitparameter.GitParameterDefinition",  # Git parameters
                ".//org.biouno.unochoice.ChoiceParameter",  # Dynamic choice parameters
                # Add more parameter types as needed
            ]
            
            for path in param_paths:
                for param in root.findall(path):
                    param_type = param.tag.split(".")[-1]
                    param_name = param.find("name").text
                    param_desc = param.find("description")
                    param_default = param.find("defaultValue")
                    
                    description = param_desc.text if param_desc is not None else ""
                    default_value = param_default.text if param_default is not None else None
                    
                    param_config = {
                        "type": self._map_jenkins_type_to_kubiya(param_type),
                        "description": self._enhance_parameter_description(
                            description, param_type, default_value
                        ),
                        "required": True,  # Jenkins parameters are typically required
                        "default": default_value
                    }
                    
                    # Handle choices for choice parameters
                    choices = None
                    if param_type == "ChoiceParameterDefinition":
                        choices_elem = param.find("choices")
                        if choices_elem is not None:
                            choices = [choice.text for choice in choices_elem.findall(".//string")]
                            # Include choices in description instead of separate field
                            param_config["description"] = self._enhance_parameter_description(
                                description, param_type, default_value, choices
                            )
                    else:
                        param_config["description"] = self._enhance_parameter_description(
                            description, param_type, default_value
                        )
                    
                    parameters[param_name] = param_config
            
            return parameters
            
        except ET.ParseError as e:
            logger.error(f"Failed to parse XML for job {job_name}: {str(e)}")
            return {}
        except Exception as e:
            logger.error(f"Error processing parameters for job {job_name}: {str(e)}")
            return {}

    def _enhance_parameter_description(
        self, description: str, param_type: str, default_value: Any, choices: Optional[List[str]] = None
    ) -> str:
        """Enhance parameter description with type information and examples."""
        enhanced_desc = description or "No description provided"
        
        # Add type-specific information
        type_info = {
            "StringParameterDefinition": {
                "info": "Text input",
                "example": "example-value"
            },
            "TextParameterDefinition": {
                "info": "Multi-line text input",
                "format": "Use JSON string format for multi-line text, e.g., \"line1\\nline2\"",
                "example": '{"content": "line1\\nline2"}'
            },
            "BooleanParameterDefinition": {
                "info": "Boolean value",
                "format": "Use 'true' or 'false' (case-insensitive)",
                "example": "true"
            },
            "ChoiceParameterDefinition": {
                "info": "Select from predefined choices",
                "format": "Provide one of the allowed values",
                "example": "choice1"
            },
            "CredentialsParameterDefinition": {
                "info": "Jenkins credentials ID",
                "format": "Provide the credentials ID string",
                "example": "jenkins-cred-id"
            },
            "GitParameterDefinition": {
                "info": "Git reference",
                "format": "Provide branch name, tag, or commit hash",
                "example": "main"
            },
            "FileParameterDefinition": {
                "info": "File content",
                "format": "Provide file content as JSON string",
                "example": '{"content": "file contents here"}'
            },
            "ListParameterDefinition": {
                "info": "List of values",
                "format": "Provide as JSON array string",
                "example": '["item1", "item2"]'
            },
            "MapParameterDefinition": {
                "info": "Key-value pairs",
                "format": "Provide as JSON object string",
                "example": '{"key1": "value1", "key2": "value2"}'
            }
        }
        
        if param_type in type_info:
            info = type_info[param_type]
            enhanced_desc += f"\n\nType: {info['info']}"
            if 'format' in info:
                enhanced_desc += f"\nFormat: {info['format']}"
            enhanced_desc += f"\nExample: {info['example']}"
            
            # Add choices if available
            if choices:
                choices_str = ', '.join(f'"{choice}"' for choice in choices)
                enhanced_desc += f"\nAllowed values: [{choices_str}]"
            
            if default_value:
                if isinstance(default_value, (dict, list)):
                    default_str = json.dumps(default_value)
                else:
                    default_str = str(default_value)
                enhanced_desc += f"\nDefault: {default_str}"
        
        return enhanced_desc

    def _map_jenkins_type_to_kubiya(self, jenkins_type: str) -> str:
        """Map Jenkins parameter types to Kubiya types."""
        # All types are mapped to str since we handle conversion in the runner
        return "str"

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