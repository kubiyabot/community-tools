# Demo Tools for Kubiya

This module provides tools for generating demo data for testing and demonstration purposes.

## Tools

### Error Spike Generator

Generates sample error spike data by sending 10 error log entries to Datadog.

### Faulty Deployment Generator

Generates sample faulty deployment data by sending 10 deployment failure log entries to Datadog.

## Prerequisites

- Datadog API key (`DD_API_KEY`)
- Datadog site URL (`DD_SITE`, defaults to datadoghq.com)

## Installation

```bash
pip install -r requirements.txt
```

## Usage

The tools can be used through the Kubiya platform:

1. Error Spike: `generate_error_spike`
2. Faulty Deployment: `generate_faulty_deployment`

Both tools will generate 10 log entries with a 2-second delay between each entry. 