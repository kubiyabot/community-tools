import logging
import json
from typing import Dict, Any, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from urllib.parse import urljoin
import base64
import os
import re
logger = logging.getLogger(__name__)

os.environ['JENKINS_API_TOKEN'] = "KYlJppNVnJQP5K1r"

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

    def _sanitize_name(self, name: str, max_length: int = 50) -> str:
        """
        Sanitize and normalize parameter names.
        
        Args:
            name: The original parameter name
            max_length: Maximum allowed length for the name (default: 50)
        
        Returns:
            Sanitized and normalized name
        """
        if not name:
            return ""
        
        # Replace spaces, dashes, and other special characters with underscores
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', name)
        
        # Replace multiple underscores with a single underscore
        sanitized = re.sub(r'_+', '_', sanitized)
        
        # Remove leading/trailing underscores
        sanitized = sanitized.strip('_')
        
        # Convert to lowercase for consistency
        sanitized = sanitized.lower()
        
        # Truncate if too long, but keep it meaningful
        if len(sanitized) > max_length:
            # Keep the first and last parts if we need to truncate
            parts = sanitized.split('_')
            if len(parts) > 2:
                # Keep first and last part
                sanitized = f"{parts[0]}_{parts[-1]}"
            else:
                # Just truncate
                sanitized = sanitized[:max_length]
        
        return sanitized

    def _process_single_job(self, job_name: str) -> Optional[Dict[str, Any]]:
        """Process a single Jenkins job."""
        try:
            # Get job info with parameters using JSON API
            info_endpoint = f'job/{job_name}/api/json?tree=description,url,buildable,property[*],lastBuild[*],lastSuccessfulBuild[*],healthReport[*],actions[parameterDefinitions]'
            job_info = self._make_request(info_endpoint)
            
            if not job_info:
                raise Exception("Failed to get job information")

            # Extract parameters from job properties
            parameters = {}
            
            # Try different paths to find parameters
            param_sources = [
                # Standard property path
                job_info.get('property', []),
                # Actions path (sometimes parameters are here)
                job_info.get('actions', []),
                # Direct parameterDefinitions (older Jenkins versions)
                [{'parameterDefinitions': job_info.get('parameterDefinitions', [])}]
            ]

            for source in param_sources:
                for prop in source:
                    if 'parameterDefinitions' in prop:
                        logger.debug(f"Found parameters for job {job_name}: {json.dumps(prop['parameterDefinitions'], indent=2)}")
                        for param in prop['parameterDefinitions']:
                            # Log the raw parameter data for debugging
                            logger.debug(f"Raw parameter data: {json.dumps(param, indent=2)}")
                            
                            # Try to get parameter name from different possible locations
                            param_name = (
                                param.get('name') or 
                                param.get('parameterName') or 
                                param.get('id') or 
                                param.get('displayName') or
                                # Try to extract from defaultParameterValue if exists
                                (param.get('defaultParameterValue', {}) or {}).get('name')
                            )
                            
                            if not param_name:
                                # Try to generate a name based on type if no name found
                                param_type = param.get('_class', '').split('.')[-1]
                                param_count = len(parameters) + 1
                                param_name = f"param_{param_type.lower()}_{param_count}"
                                logger.warning(
                                    f"Generated name '{param_name}' for unnamed parameter in job {job_name}.\n"
                                    f"Parameter type: {param_type}\n"
                                    f"Raw data: {json.dumps(param, indent=2)}"
                                )

                            param_type = param.get('_class', '').split('.')[-1]
                            logger.debug(f"Processing parameter: {param_name} of type {param_type}")
                            
                            # Map Jenkins parameter types to Kubiya types
                            type_mapping = {
                                'BooleanParameterDefinition': 'bool',
                                'StringParameterDefinition': 'str',
                                'TextParameterDefinition': 'str',
                                'ChoiceParameterDefinition': 'str',
                                'PasswordParameterDefinition': 'str',
                                'FileParameterDefinition': 'str',
                            }
                            
                            # Build parameter description
                            description = param.get('description', 'No description provided')
                            if 'choices' in param:
                                choices_str = ', '.join(f'"{choice}"' for choice in param['choices'])
                                description += f"\nAllowed values: [{choices_str}]"
                            
                            param_config = {
                                "name": param_name,
                                "original_name": param_name,  # Store original name for unsanitization
                                "type": type_mapping.get(param_type, 'str'),
                                "description": description,
                                "required": not bool(param.get('defaultValue'))
                            }

                            # Handle default values based on type
                            if 'defaultValue' in param:
                                if param_type == 'BooleanParameterDefinition':
                                    param_config['default'] = str(param['defaultValue']).lower() == 'true'
                                else:
                                    param_config['default'] = param['defaultValue']
                            # Also check defaultParameterValue (alternative location)
                            elif 'defaultParameterValue' in param:
                                default_value = param['defaultParameterValue'].get('value')
                                if default_value is not None:
                                    if param_type == 'BooleanParameterDefinition':
                                        param_config['default'] = str(default_value).lower() == 'true'
                                    else:
                                        param_config['default'] = default_value

                            # Add choices if available
                            if 'choices' in param:
                                param_config['choices'] = param['choices']
                            
                            parameters[param_name] = param_config
                            logger.debug(f"Added parameter config: {param_config}")

            # Add job URL to description
            job_description = job_info.get('description', '')
            if job_description:
                job_description += f"\n\nJenkins Job URL: {self.jenkins_url}/job/{job_name}"
            else:
                job_description = f"Jenkins Job URL: {self.jenkins_url}/job/{job_name}"

            result = {
                "name": job_name,
                "description": job_description,
                "parameters": parameters,
                "url": job_info.get('url', ''),
                "buildable": job_info.get('buildable', True),
                "type": self._determine_job_type(job_info),
                "health": self._get_job_health(job_info),
                "auth": {
                    "username": self.username
                }
            }
            
            logger.debug(f"Processed job {job_name} with parameters: {parameters}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to process job {job_name}: {str(e)}")
            return None

    def _extract_parameters_from_properties(self, properties: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract parameters from job properties using JSON API."""
        parameters = {}
        
        for prop in properties:
            # Handle ParametersDefinitionProperty
            if 'parameterDefinitions' in prop:
                for param in prop['parameterDefinitions']:
                    param_type = param.get('_class', '').split('.')[-1]
                    param_name = param.get('name', '')
                    
                    param_config = {
                        "type": "str",  # All parameters are strings in Kubiya
                        "name": param_name,
                        "description": self._enhance_parameter_description(
                            param.get('description', ''),
                            param_type,
                            param.get('defaultValue'),
                            param.get('choices', []) if 'choices' in param else None
                        ),
                        "required": True,  # Jenkins parameters are typically required
                        "default": param.get('defaultValue')
                    }
                    
                    parameters[param_name] = param_config
        
        return parameters

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

    def _get_all_jobs_recursive(self, url: str = None) -> List[Dict[str, str]]:
        """Recursively get all jobs from Jenkins, including those in folders."""
        try:
            if url is None:
                url = f"{self.jenkins_url}/api/json"
            
            logger.debug(f"Fetching jobs from: {url}")
            response = self._make_request(url)
            
            if not response:
                logger.warning(f"No response from {url}")
                return []

            jobs = []
            for item in response.get('jobs', []):
                try:
                    item_class = item.get('_class', '')
                    item_name = item.get('name', '')
                    item_url = item.get('url', '')
                    
                    logger.debug(f"Processing item: {item_name} ({item_class})")
                    
                    # Handle different job types
                    if any(job_type in item_class for job_type in ['WorkflowJob', 'FreeStyleProject', 'Pipeline']):
                        # Regular job
                        jobs.append({
                            'name': item_name,
                            'full_name': item.get('fullName', item_name),
                            'url': item_url,
                            'class': item_class
                        })
                        logger.debug(f"Added job: {item_name}")
                        
                    elif any(folder_type in item_class for folder_type in ['Folder', 'WorkflowMultiBranch', 'OrganizationFolder']):
                        # Folder or similar container - recurse into it
                        logger.debug(f"Recursing into folder: {item_name}")
                        sub_jobs = self._get_all_jobs_recursive(f"{item_url}api/json")
                        jobs.extend(sub_jobs)
                        
                except Exception as e:
                    error_msg = f"Error processing job {item_name}: {str(e)}"
                    logger.error(error_msg)
                    self.errors.append(error_msg)
                    continue

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
            
            if not all_jobs:
                logger.warning("No jobs found in Jenkins")
                self.warnings.append("No jobs were found in Jenkins server")
                return {}, self.warnings, self.errors

            logger.info(f"Found {len(all_jobs)} total jobs")
            
            # Filter jobs if needed
            jobs_to_process = [
                job for job in all_jobs
                if not job_filter or job['full_name'] in job_filter
            ]
            
            if job_filter and not jobs_to_process:
                warning_msg = f"No jobs matched the filter: {job_filter}"
                logger.warning(warning_msg)
                self.warnings.append(warning_msg)
                return {}, self.warnings, self.errors

            logger.info(f"Processing {len(jobs_to_process)} jobs after filtering")

            # Process jobs in parallel
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_job = {
                    executor.submit(self._process_single_job, job['full_name']): job
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