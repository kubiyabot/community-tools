# Kubiya ArgoCD Tools

A collection of tools for interacting with ArgoCD through the Kubiya platform.

## Installation

```bash
pip install -e .
```

## Usage

```python
from argocd_tools import (
    argocd_login,
    argocd_list_applications,
    argocd_get_application,
    argocd_sync_application,
    argocd_create_application,
    argocd_delete_application,
    argocd_rollback_application,
    argocd_set_app_parameters,
    argocd_get_project,
    argocd_create_project,
    argocd_delete_project,
    argocd_list_repositories,
    argocd_add_repository,
)

# Use the tools as needed
```

## Available Tools

- `argocd_login`: Login to ArgoCD server
- `argocd_list_applications`: List ArgoCD applications with detailed output
- `argocd_get_application`: Get detailed information of an ArgoCD application
- `argocd_sync_application`: Sync an ArgoCD application with advanced options
- `argocd_create_application`: Create a new ArgoCD application with advanced configuration
- `argocd_delete_application`: Delete an ArgoCD application with advanced options
- `argocd_rollback_application`: Rollback an ArgoCD application to a previous version
- `argocd_set_app_parameters`: Set parameters for an ArgoCD application
- `argocd_get_project`: Get detailed information of an ArgoCD project
- `argocd_create_project`: Create a new ArgoCD project with advanced configuration
- `argocd_delete_project`: Delete an ArgoCD project
- `argocd_list_repositories`: List configured Git repositories in ArgoCD
- `argocd_add_repository`: Add a new Git repository to ArgoCD

## Development

To develop or contribute to this package:

1. Clone the repository
2. Install in development mode: `pip install -e .`
3. Make your changes
4. Test your changes: `python test_imports.py` 