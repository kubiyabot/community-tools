# Honeycomb Tools Module for Kubiya SDK

This module provides tools for interacting with Honeycomb using the Kubiya SDK. These tools allow you to analyze traces and metrics from your Honeycomb datasets.

## Configuration

The module requires a Honeycomb API key to be set in the environment:
- `HONEYCOMB_API_KEY`: Your Honeycomb API key

## Tools Overview

1. **analyze_traces**: Analyze traces for a specific service in a Honeycomb dataset
   - Get P99 latency
   - Count total traces
   - Filter by service name
   - Specify time range

## Usage

To use these tools in your Kubiya SDK workflows, first add this module as a source in your Teammate Environment. Then, you can use the tools in your workflows. 