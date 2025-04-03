# Honeycomb Tools Module for Kubiya SDK

This module provides Docker-based tools for interacting with Honeycomb using the Kubiya SDK. These tools allow you to analyze traces and metrics from your Honeycomb datasets.

## Configuration

The module requires a Honeycomb API key to be set in the environment:
- `HONEYCOMB_API_KEY`: Your Honeycomb API key

## Tools Overview

1. **analyze_traces**: Analyze traces for a specific service in a Honeycomb dataset
   - Get P99 latency
   - Count total traces
   - Filter by service name
   - Specify time range

## Technical Details

- Tools are executed in a Docker container using `curlimages/curl:8.1.2` as the base image
- Each tool installs necessary dependencies (jq, Python3) at runtime
- API requests are made using curl with proper authentication headers

## Usage

To use these tools in your Kubiya SDK workflows:

1. Add this module as a source in your Teammate Environment
2. Configure the HONEYCOMB_API_KEY secret
3. Use the tools in your workflows:

Example:
```bash
analyze_traces --dataset="prod" --service_name="api" --start_time=60
``` 