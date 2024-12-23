#!/usr/bin/env python
import jinja2
from jinja2 import Environment, select_autoescape
import os
import sys
import json
import logging
from pathlib import Path

from .template_handler import TemplateHandler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def parse_workflow_steps(steps_json: str) -> list:
    """Parse workflow steps from JSON string."""
    try:
        return json.loads(steps_json)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid workflow steps JSON: {e}")
        sys.exit(1)

def parse_failures(failures_json: str) -> list:
    """Parse workflow failures from JSON string."""
    try:
        return json.loads(failures_json)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid failures JSON: {e}")
        sys.exit(1)

def parse_fixes(fixes_json: str) -> list:
    """Parse workflow fixes from JSON string."""
    try:
        return json.loads(fixes_json)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid fixes JSON: {e}")
        sys.exit(1)

def parse_run_details(details_json: str) -> dict:
    """Parse workflow run details from JSON string."""
    try:
        return json.loads(details_json)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid run details JSON: {e}")
        sys.exit(1)

def find_template_file() -> Path:
    """Find the workflow failure template file."""
    possible_paths = [
        # Check relative to script location
        Path(__file__).parent / 'templating' / 'templates' / 'workflow_failure.jinja2',
        Path(__file__).parent / 'utils' / 'templating' / 'templates' / 'workflow_failure.jinja2',
        # Check in /opt/scripts path (Docker container)
        Path('/opt/scripts/templating/templates/workflow_failure.jinja2'),
        Path('/opt/scripts/utils/templating/templates/workflow_failure.jinja2'),
    ]
    
    for path in possible_paths:
        if path.exists():
            logger.info(f"Found template at: {path}")
            return path
            
    raise FileNotFoundError("Could not find workflow_failure.jinja2 template in any expected location")

def generate_comment(variables: dict) -> str:
    """Generate a comment using the workflow failure template."""
    try:
        # Parse JSON inputs
        workflow_steps = parse_workflow_steps(variables['workflow_steps'])
        failures = parse_failures(variables['failures'])
        fixes = parse_fixes(variables['fixes'])
        run_details = parse_run_details(variables['run_details'])

        # Create template context
        context = {
            'workflow_name': run_details.get('name', 'Unknown Workflow'),
            'failed_steps': [failure['step'] for failure in failures],
            'failures': failures,  # Pass the full failures list directly
            'fixes': fixes,  # Pass the full fixes list directly 
            'workflow_steps': [step['name'] for step in workflow_steps],
            'error_logs': variables['error_logs'],
            'run_details': json.dumps(run_details),  # Pass as JSON string
            'number': variables['pr_number'],
            'repo': variables['repo']
        }
        logger.info(f"context: {context}")

        # Initialize template handler
        template_handler = TemplateHandler()

        logger.info(f"Available templates: {template_handler.get_available_templates()}")

        # Render the template
        comment = template_handler.render_template('workflow_failure', context)

        if not comment:
            raise ValueError("Failed to generate comment from template")
            
        logger.info("Successfully generated comment")
        return comment

    except Exception as e:
        logger.error(f"Error generating comment: {str(e)}")
        sys.exit(1)

def main():
    """Main function to handle comment generation."""
    try:
        # Get variables from environment
        required_vars = [
            'REPO', 'PR_NUMBER', 'WORKFLOW_STEPS', 
            'FAILURES', 'FIXES', 'ERROR_LOGS', 'RUN_DETAILS'
        ]
        
        variables = {}
        for var in required_vars:
            if var not in os.environ:
                raise KeyError(f"Missing required environment variable: {var}")
            variables[var.lower()] = os.environ[var]
        
        logger.info("Starting comment generation...")
        comment = generate_comment(variables)
        print(comment)
        logger.info("Comment generation completed successfully")
        
    except KeyError as e:
        logger.error(f"Missing environment variable: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
