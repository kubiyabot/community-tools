# AWS CLI Tool

## Description

The `aws_cli` tool allows you to run AWS CLI commands using the `amazon/aws-cli` Docker image. This tool is designed to interact with AWS services by running commands provided by the AWS CLI.

## Usage

### Arguments

- **command**: The AWS CLI command to run (e.g., `s3 ls`). This argument is required.

### Environment Variables

The tool requires the following environment variable to be set:

- **AWS_PROFILE**: The AWS profile to use from your AWS credentials file.

## File Mappings

The tool requires access to your AWS credentials. The following file mapping is used to provide the necessary credentials:

- **Source**: `/home/appuser/.aws/credentials`
- **Destination**: `/root/.aws/credentials`

## License

This tool is licensed under the MIT License. See the LICENSE file for more details.
