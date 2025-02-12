from kubiya_sdk.tools.models import Arg
from .base import ScoutTool

def create_aws_scan_tool():
    """Create AWS scanning tool."""
    return ScoutTool(
        name="aws_security_scan",
        description="Run ScoutSuite security scan on AWS environment",
        args=[
            Arg(
                name="services",
                type="str",
                description="Comma-separated list of services to scan (e.g., 'ec2,s3,rds'). Leave empty to scan all services.",
                required=False
            ),
            Arg(
                name="regions",
                type="str",
                description="Comma-separated list of regions to scan (e.g., 'us-east-1,eu-west-1'). Leave empty to scan all regions.",
                required=False
            ),
            Arg(
                name="report_name",
                type="str",
                description="Name for the report file (default: scout-report)",
                required=False,
                default="scout-report"
            ),
            Arg(
                name="report_format",
                type="str",
                description="Format for the report (json or html)",
                required=False,
                default="html"
            ),
            Arg(
                name="excluded_services",
                type="str",
                description="Comma-separated list of services to exclude from the scan",
                required=False
            ),
            # New authentication arguments
            Arg(
                name="aws_profile",
                type="str",
                description="AWS profile name to use from credentials file",
                required=False
            ),
            Arg(
                name="aws_access_key_id",
                type="str",
                description="AWS access key ID for direct authentication",
                required=False
            ),
            Arg(
                name="aws_secret_access_key",
                type="str",
                description="AWS secret access key for direct authentication",
                required=False
            ),
            Arg(
                name="aws_session_token",
                type="str",
                description="AWS session token for temporary credentials",
                required=False
            ),
            Arg(
                name="assume_role_arn",
                type="str",
                description="ARN of IAM role to assume",
                required=False
            ),
            Arg(
                name="mfa_serial",
                type="str",
                description="MFA device serial number for authentication",
                required=False
            ),
            Arg(
                name="mfa_token",
                type="str",
                description="MFA token code",
                required=False
            ),
            Arg(
                name="credentials_file",
                type="str",
                description="Path to AWS credentials file (default: ~/.aws/credentials)",
                required=False
            )
        ],
        content="""
#!/bin/bash
set -e

# Source virtual environment
. /opt/venv/bin/activate

# Create scout.py file
cat > /opt/scout.py << 'EOL'
#!/usr/bin/env python3
import os
import boto3
from ScoutSuite.core.cli_parser import ScoutSuiteArgumentParser
from ScoutSuite.core.console_manager import AWSConsoleManager
from ScoutSuite.core.processingengine import ProcessingEngine
from ScoutSuite.core.ruleset import Ruleset
from ScoutSuite.core.exceptions import RulesetError
from ScoutSuite.providers.aws.provider import AWSProvider

def get_session():
    """Create AWS session with appropriate credentials"""
    session_kwargs = {}
    
    # Direct credentials take precedence
    if os.getenv('AWS_ACCESS_KEY_ID') and os.getenv('AWS_SECRET_ACCESS_KEY'):
        session_kwargs.update({
            'aws_access_key_id': os.getenv('AWS_ACCESS_KEY_ID'),
            'aws_secret_access_key': os.getenv('AWS_SECRET_ACCESS_KEY'),
            'aws_session_token': os.getenv('AWS_SESSION_TOKEN')
        })
    
    # Create initial session
    session = boto3.Session(**session_kwargs)
    
    # Handle role assumption if specified
    if os.getenv('ASSUME_ROLE_ARN'):
        sts = session.client('sts')
        assume_role_kwargs = {
            'RoleArn': os.getenv('ASSUME_ROLE_ARN'),
            'RoleSessionName': 'ScoutSuite'
        }
        
        # Add MFA if specified
        if os.getenv('MFA_SERIAL') and os.getenv('MFA_TOKEN'):
            assume_role_kwargs.update({
                'SerialNumber': os.getenv('MFA_SERIAL'),
                'TokenCode': os.getenv('MFA_TOKEN')
            })
            
        credentials = sts.assume_role(**assume_role_kwargs)['Credentials']
        session = boto3.Session(
            aws_access_key_id=credentials['AccessKeyId'],
            aws_secret_access_key=credentials['SecretAccessKey'],
            aws_session_token=credentials['SessionToken']
        )
    
    return session

def run_scout():
    parser = ScoutSuiteArgumentParser()
    args = parser.parse_args()
    
    # Get AWS session with appropriate credentials
    session = get_session()
    
    # Configure provider with session
    provider = AWSProvider(session=session)
    
    # Execute run
    report = provider.run(
        services=args.services.split(',') if args.services else None,
        regions=args.regions.split(',') if args.regions else None,
        excluded_services=args.excluded_services.split(',') if args.excluded_services else None
    )

    # Create report
    report_name = args.report_name or 'scout-report'
    report.save(report_name, args.report_format)

if __name__ == '__main__':
    run_scout()
EOL

chmod +x /opt/scout.py

# Set up AWS credentials environment
if [ ! -z "{{.aws_access_key_id}}" ] && [ ! -z "{{.aws_secret_access_key}}" ]; then
    export AWS_ACCESS_KEY_ID="{{.aws_access_key_id}}"
    export AWS_SECRET_ACCESS_KEY="{{.aws_secret_access_key}}"
    if [ ! -z "{{.aws_session_token}}" ]; then
        export AWS_SESSION_TOKEN="{{.aws_session_token}}"
    fi
fi

if [ ! -z "{{.assume_role_arn}}" ]; then
    export ASSUME_ROLE_ARN="{{.assume_role_arn}}"
fi

if [ ! -z "{{.mfa_serial}}" ] && [ ! -z "{{.mfa_token}}" ]; then
    export MFA_SERIAL="{{.mfa_serial}}"
    export MFA_TOKEN="{{.mfa_token}}"
fi

# Configure AWS credentials file if specified
if [ ! -z "{{.credentials_file}}" ]; then
    mkdir -p ~/.aws
    cp "{{.credentials_file}}" ~/.aws/credentials
fi

# Build Scout command
SCOUT_CMD="/opt/scout.py aws"

# Add AWS profile if specified
if [ ! -z "{{.aws_profile}}" ]; then
    export AWS_PROFILE="{{.aws_profile}}"
fi

# Add services if specified
if [ ! -z "{{.services}}" ]; then
    SCOUT_CMD="$SCOUT_CMD --services {{.services}}"
fi

# Add regions if specified
if [ ! -z "{{.regions}}" ]; then
    SCOUT_CMD="$SCOUT_CMD --regions {{.regions}}"
fi

# Add excluded services if specified
if [ ! -z "{{.excluded_services}}" ]; then
    SCOUT_CMD="$SCOUT_CMD --excluded-services {{.excluded_services}}"
fi

# Configure report format and name
REPORT_DIR="/tmp/scout-report"
mkdir -p $REPORT_DIR

if [ "{{.report_format}}" == "json" ]; then
    SCOUT_CMD="$SCOUT_CMD --report-format json --report-name $REPORT_DIR/{{.report_name}}"
else
    SCOUT_CMD="$SCOUT_CMD --report-format html --report-name $REPORT_DIR/{{.report_name}}"
fi

echo "🔍 Starting ScoutSuite security scan..."
echo "Command: $SCOUT_CMD"

# Run Scout
python $SCOUT_CMD

# Check if scan was successful
if [ $? -eq 0 ]; then
    echo "✅ Scan completed successfully!"
    
    # Print report location
    if [ "{{.report_format}}" == "json" ]; then
        echo "📊 JSON Report:"
        cat "$REPORT_DIR/{{.report_name}}.json"
    else
        echo "📊 HTML Report generated at: $REPORT_DIR/{{.report_name}}.html"
        echo "You can find the report in the $REPORT_DIR directory"
    fi
else
    echo "❌ Scan failed!"
    exit 1
fi
"""
    )

# Create tool instance
aws_scan_tool = create_aws_scan_tool()

__all__ = ['aws_scan_tool'] 