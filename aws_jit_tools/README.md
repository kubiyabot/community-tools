# AWS JIT (Just-In-Time) Access Tools

A collection of tools for managing Just-In-Time AWS access through IAM Identity Center (SSO) permission sets. This package automatically generates Kubiya tools based on your access configuration.

## Features

- Dynamic tool generation from JSON configuration
- Integration with AWS IAM Identity Center (SSO)
- Automatic permission set assignments
- Clean separation of configuration and implementation

## Prerequisites

1. AWS IAM Identity Center (SSO) must be configured in your AWS account
2. Permission sets must be pre-created in IAM Identity Center
3. Users must exist in your Identity Center directory
4. Required AWS permissions (see below)

## Required AWS Permissions

The AWS profile used needs the following permissions:

## Usage

Import and initialize the tools in your Kubiya environment:
