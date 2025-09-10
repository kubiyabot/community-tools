# OpenShift CLI Tools

A unified OpenShift CLI tool that provides seamless access to any `oc` command with automatic in-cluster context handling.

## Features

- **Universal CLI Access**: Execute any OpenShift CLI command through a single tool
- **Automatic Context**: Handles in-cluster authentication and context setup automatically
- **Smart Output**: Truncates large outputs and provides helpful guidance  
- **LLM-Friendly**: Comprehensive examples and usage patterns for AI assistants

## Tool

### `oc`

Executes any OpenShift CLI command with automatic in-cluster context handling.

**Parameters:**
- `command` (required): The OpenShift CLI command to execute (without the `oc` prefix)

**Examples:**
- `get pod my-pod-name -n my-project`
- `get pods -l app=my-app -n prod` 
- `get projects`
- `get routes -n my-project`
- `logs deployment/my-app -n my-project`
- `status -n my-project`

## Installation

```bash
pip install -r requirements.txt
```

## Usage

The tool automatically handles:
- In-cluster authentication using service account tokens
- Context configuration for OpenShift clusters
- Output formatting and truncation
- Error handling and validation
