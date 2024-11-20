#!/usr/bin/env python3
import json
import logging
import boto3
import argparse
from typing import Dict, Any
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

class S3PolicyManager:
    def __init__(self, profile_name: str = None):
        """Initialize S3 policy manager with optional profile."""
        self.session = boto3.Session(profile_name=profile_name)
        self.s3_client = self.session.client('s3')

    def create_bucket_policy(self, bucket_name: str, policy: Dict[str, Any], account_id: str) -> bool:
        """
        Create or update an S3 bucket policy.
        Returns True if successful, raises exception if failed.
        """
        try:
            # Convert policy to string if it's a dict
            if isinstance(policy, dict):
                policy = json.dumps(policy)
            
            # Replace any placeholder account IDs with the provided one
            policy = policy.replace("${AWS::AccountId}", account_id)
            
            # Put bucket policy
            self.s3_client.put_bucket_policy(
                Bucket=bucket_name,
                Policy=policy
            )
            
            logger.info(f"Successfully applied policy to bucket: {bucket_name}")
            return True
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"Failed to apply bucket policy: {error_code} - {error_message}")
            raise
        except Exception as e:
            logger.error(f"Error creating bucket policy: {str(e)}")
            raise

def main():
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(description='Manage S3 bucket policies')
    parser.add_argument('--profile', help='AWS profile name')
    parser.add_argument('--bucket', required=True, help='Name of the S3 bucket')
    parser.add_argument('--policy-file', required=True, help='Path to JSON policy file')
    parser.add_argument('--account-id', required=True, help='AWS account ID')
    
    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(level=logging.INFO)

    try:
        # Read policy from file
        with open(args.policy_file, 'r') as f:
            policy = json.load(f)

        # Create S3PolicyManager instance and apply policy
        manager = S3PolicyManager(profile_name=args.profile)
        manager.create_bucket_policy(args.bucket, policy, args.account_id)

    except Exception as e:
        logger.error(f"Failed to apply bucket policy: {str(e)}")
        raise

if __name__ == '__main__':
    main()

# Example usage:
# 1. Create a JSON file named 'policy.json' with your S3 bucket policy:
#    {
#      "Version": "2012-10-17",
#      "Statement": [
#        {
#          "Sid": "PublicRead",
#          "Effect": "Allow",
#          "Principal": "*",
#          "Action": ["s3:GetObject"],
#          "Resource": ["arn:aws:s3:::example-bucket/*"]
#        }
#      ]
#    }
#
# 2. Run the script:
#    python s3_request.py --profile my-aws-profile --bucket my-bucket-name --policy-file ./policy.json --account-id 123456789012
