# HubSpot Tools for Kubiya

This module provides integration with HubSpot CRM platform, allowing common operations such as:

- Contact management (create, update, delete, search)
- Company management
- Deal management
- Pipeline operations
- Custom object operations
- Email marketing operations

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

The following environment variables are required:
- `HUBSPOT_ACCESS_TOKEN`: Your HubSpot API access token

## Usage

Import and use the tools in your Kubiya workflows:

```python
from hubspot_tools.tools import ContactsTool, CompaniesTool, DealsTool
``` 