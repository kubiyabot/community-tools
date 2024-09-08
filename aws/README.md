# AWS Tools Module for Kubiya SDK

This module provides a comprehensive set of tools for interacting with AWS services using the Kubiya SDK. These tools are designed to be stateless and easily discoverable by the Kubiya engine, allowing for dynamic execution in various environments with different AWS configurations.

## Tools Overview

1. **EC2**: Manages EC2 instances (describe, start, stop, terminate, create tags)
2. **S3**: Manages S3 buckets and objects (list, copy, move, remove)
3. **Other AWS services**: (Add more services as implemented)

## Configuration

This module uses AWS credentials stored in the `~/.aws/credentials` and `~/.aws/config` files. Make sure these files are properly configured with your AWS access key ID, secret access key, and default region.

## Usage

To use these tools in your Kubiya SDK workflows, first add this module as a source in your Teammate Environment. Then, you can use the tools in your workflows like this:
