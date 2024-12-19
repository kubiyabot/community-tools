#!/usr/bin/env python3
import os
import sys
import json
import logging
from pathlib import Path
from utils.templating.template_handler import TemplateHandler
from utils.templating.schema import WorkflowStep, WorkflowFailure, WorkflowFix, WorkflowRunDetails

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def parse_workflow_steps(steps_json: str) -> list[WorkflowStep]:
    """Parse workflow steps from JSON string."""
    try:
        return json.loads(steps_json)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid workflow steps JSON: {e}")
        sys.exit(1)

def parse_failures(failures_json: str) -> list[WorkflowFailure]:
    """Parse workflow failures from JSON string."""
    try:
        return json.loads(failures_json)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid failures JSON: {e}")
        sys.exit(1)

def parse_fixes(fixes_json: str) -> list[WorkflowFix]:
    """Parse workflow fixes from JSON string."""
    try:
        return json.loads(fixes_json)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid fixes JSON: {e}")
        sys.exit(1)

def parse_run_details(details_json: str) -> WorkflowRunDetails:
    """Parse workflow run details from JSON string."""
    try:
        return json.loads(details_json)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid run details JSON: {e}")
        sys.exit(1)

def generate_comment(variables: dict) -> str:
    """Generate a comment using the workflow failure template."""
    try:
        # Parse JSON inputs
        workflow_steps = parse_workflow_steps(variables['workflow_steps'])
        failures = parse_failures(variables['failures'])
        fixes = parse_fixes(variables['fixes'])
        run_details = parse_run_details(variables['run_details'])

        # Create template context with parsed data
        context = {
            'repo': variables['repo'],
            'number': variables['pr_number'],
            'workflow_steps': workflow_steps,
            'failures': failures,
            'fixes': fixes,
            'run_details': run_details,
            'error_logs': variables['error_logs']
        }

        handler = TemplateHandler()
        comment = handler.render_template('workflow_failure', context)
        if not comment:
            raise ValueError("Failed to generate comment from template")
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
        
        comment = generate_comment(variables)
        print(comment)
        
    except KeyError as e:
        logger.error(str(e))
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 