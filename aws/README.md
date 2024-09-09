# AWS Tools Module for Kubiya SDK

This module provides a comprehensive set of tools for interacting with AWS services using the Kubiya SDK. These tools are designed to be stateless and easily discoverable by the Kubiya engine, allowing for dynamic execution in various environments with different AWS configurations.

## Tools Overview

1. **EC2**: Manages EC2 instances (describe, start, stop, terminate, create, list types, create image, list images, modify instance, manage security groups)
2. **S3**: Manages S3 buckets and objects (list, copy, move, remove, sync, create/delete buckets, presign URLs, configure website, set policies and versioning, manage multipart uploads)
3. **RDS**: Manages RDS databases (create, delete, describe, modify, start, stop, reboot, create/list/restore snapshots, manage read replicas)

## Configuration

This module uses AWS credentials stored in the `~/.aws/credentials` file. Make sure this file is properly configured with your AWS access key ID and secret access key.

## Usage

To use these tools in your Kubiya SDK workflows, first add this module as a source in your Teammate Environment. Then, you can use the tools in your workflows like this:
