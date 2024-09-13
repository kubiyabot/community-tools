# MySQL Tools Module for Kubiya SDK

This module provides a set of tools for interacting with MySQL databases using SSH tunneling via the Kubiya SDK. These tools are designed to be stateless and easily discoverable by the Kubiya engine, allowing for dynamic execution in various environments with different MySQL configurations.

## Tools Overview

1. **connection**: Manages MySQL connections (connect, disconnect)
2. **query**: Executes queries and fetches results
3. **database**: Manages databases (create, drop, list)
4. **table**: Manages tables (create, drop, list)
5. **backup**: Handles database backups and restores

## Architecture and Execution Flow

[Include a Mermaid diagram similar to the Kubernetes one, adapted for MySQL]

## Usage

[Include instructions on how to add the module as a source, similar to the Kubernetes README]

### Using the Tools in Workflows

After adding the module as a source, you can use the tools in your workflows like this:
