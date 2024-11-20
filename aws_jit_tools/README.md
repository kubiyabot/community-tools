# AWS JIT (Just-In-Time) Access Tools

A collection of tools for managing Just-In-Time AWS access through IAM Identity Center (SSO) permission sets. This package automatically generates Kubiya tools based on your access configuration.

## Features

- Dynamic tool generation from JSON configuration
- Integration with AWS IAM Identity Center (SSO)
- Automatic permission set assignments and revocations
- Clean separation of configuration and implementation

## Prerequisites

1. AWS IAM Identity Center (SSO) must be configured in your AWS account
2. Permission sets must be pre-created in IAM Identity Center
3. Users must exist in your Identity Center directory
4. Required AWS permissions (see below)

## Required AWS Permissions

The AWS profile used needs the following permissions:
- `sso:ListInstances`
- `sso:ListUsers`
- `sso:DescribePermissionSet`
- `sso:CreateAccountAssignment`
- `sso:DeleteAccountAssignment`
- `iam:ListAccountAliases`

## Usage

### Grant Access

To grant access, the tool uses the `KUBIYA_USER_EMAIL` environment variable to identify the user. The tool will automatically assign the specified permission set to the user.

### Revoke Access

To revoke access, provide the user's email as an argument. The tool will remove the specified permission set from the user.

### Example Commands
