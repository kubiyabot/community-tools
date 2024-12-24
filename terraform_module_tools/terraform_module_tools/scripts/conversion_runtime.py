import json
import re
import subprocess
from typing import Dict, Any, Optional, List
import tempfile
import os
import logging

logger = logging.getLogger(__name__)

RESOURCE_TYPE_MAPPINGS = {
    'AWS::EC2::Instance': 'aws_instance',
    'AWS::EC2::VPC': 'aws_vpc',
    'AWS::EC2::Subnet': 'aws_subnet',
    'AWS::EC2::SecurityGroup': 'aws_security_group',
    'AWS::RDS::DBInstance': 'aws_db_instance',
    'AWS::S3::Bucket': 'aws_s3_bucket',
    'AWS::IAM::Role': 'aws_iam_role',
    # Add more mappings as needed
}

def run_former2_cli(region: str = None, profile: str = None, services: Optional[List[str]] = None) -> str:
    """Run Former2 CLI and return the output."""
    try:
        cmd = ['former2', 'generate', '--output-terraform', '-']
        
        if region:
            cmd.extend(['--region', region])
        if profile:
            cmd.extend(['--profile', profile])
        if services:
            cmd.extend(['--services', ','.join(services)])

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        logger.error(f"Former2 CLI failed: {e.stderr}")
        raise ValueError(f"Former2 CLI failed: {e.stderr}")
    except Exception as e:
        logger.error(f"Failed to run Former2: {str(e)}")
        raise ValueError(f"Failed to run Former2: {str(e)}")

def convert_former2_to_terraform(former2_output: str) -> str:
    """Convert Former2 JSON output to Terraform HCL."""
    try:
        # Parse Former2 JSON
        former2_data = json.loads(former2_output)
        
        # Initialize Terraform code
        tf_code = []
        
        # Add provider block with dynamic region
        region = former2_data.get('Metadata', {}).get('Region', 'us-west-2')
        tf_code.append(f'provider "aws" {{\n  region = "{region}"\n}}\n')
        
        # Convert each resource
        for resource in former2_data.get('Resources', []):
            resource_type = resource.get('Type', '')
            if not resource_type.startswith('AWS::'):
                continue
                
            # Convert resource type to Terraform format
            tf_type = _convert_resource_type(resource_type)
            if not tf_type:
                logger.warning(f"Skipping unsupported resource type: {resource_type}")
                continue
            
            # Generate resource name
            resource_name = _generate_resource_name(resource)
            
            # Convert properties to Terraform format
            properties = _convert_properties(resource.get('Properties', {}))
            
            # Generate resource block
            tf_code.append(f'resource "{tf_type}" "{resource_name}" {{')
            for k, v in properties.items():
                tf_code.append(f'  {k} = {_format_value(v)}')
            tf_code.append('}\n')
        
        return '\n'.join(tf_code)
        
    except Exception as e:
        logger.error(f"Failed to convert Former2 output: {str(e)}")
        raise ValueError(f"Failed to convert Former2 output: {str(e)}")

def _convert_resource_type(cf_type: str) -> Optional[str]:
    """Convert CloudFormation resource type to Terraform resource type."""
    return RESOURCE_TYPE_MAPPINGS.get(cf_type)

def _generate_resource_name(resource: Dict[str, Any]) -> str:
    """Generate a valid Terraform resource name."""
    # Try to get a meaningful name from tags or logical ID
    name = None
    
    # Check tags for a Name tag
    tags = resource.get('Properties', {}).get('Tags', [])
    for tag in tags:
        if tag.get('Key') == 'Name':
            name = tag.get('Value')
            break
    
    # If no name tag, use logical ID
    if not name:
        name = resource.get('LogicalId', '')
    
    # Clean the name for Terraform
    name = re.sub(r'[^a-zA-Z0-9_-]', '_', name.lower())
    name = re.sub(r'^[^a-zA-Z]', 'r', name)  # Ensure starts with letter
    
    return name or 'resource'

def _convert_properties(properties: Dict[str, Any]) -> Dict[str, Any]:
    """Convert CloudFormation properties to Terraform format."""
    result = {}
    
    for key, value in properties.items():
        # Convert camelCase to snake_case
        tf_key = re.sub('([A-Z])', r'_\1', key).lower().lstrip('_')
        
        # Handle special property conversions
        if key == 'Tags':
            result['tags'] = _convert_tags(value)
        else:
            result[tf_key] = value
            
    return result

def _convert_tags(tags: List[Dict[str, str]]) -> Dict[str, str]:
    """Convert CloudFormation tags to Terraform tags format."""
    return {tag['Key']: tag['Value'] for tag in tags}

def _format_value(value: Any) -> str:
    """Format a value for Terraform HCL."""
    if isinstance(value, bool):
        return str(value).lower()
    elif isinstance(value, (int, float)):
        return str(value)
    elif isinstance(value, dict):
        items = [f'{k} = {_format_value(v)}' for k, v in value.items()]
        return '{\n    ' + '\n    '.join(items) + '\n  }'
    elif isinstance(value, list):
        if not value:
            return '[]'
        items = [_format_value(item) for item in value]
        return '[\n    ' + ',\n    '.join(items) + '\n  ]'
    else:
        return f'"{str(value)}"'

def save_terraform_code(tf_code: str, output_dir: str, filename: str = "main.tf") -> str:
    """Save Terraform code to a file."""
    try:
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, filename)
        
        with open(output_file, 'w') as f:
            f.write(tf_code)
            
        return output_file
    except Exception as e:
        logger.error(f"Failed to save Terraform code: {str(e)}")
        raise ValueError(f"Failed to save Terraform code: {str(e)}") 