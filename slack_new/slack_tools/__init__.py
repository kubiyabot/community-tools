"""
Slack Tools for Kubiya SDK

This module provides tools for interacting with Slack channels and messages
using dual token support for enhanced permissions and functionality.

Features:
- Channel discovery using high-tier Slack app token
- Message posting using Kubiya integration token
- Support for public, private channels, DMs, and group DMs
- Rate limiting and comprehensive error handling
- Thread replies and Slack markdown support

Example usage:
    slack_find_channel_by_name --channel_name "general"
    slack_send_message --channel "C1234567890" --message "Hello from Kubiya!"
"""

from .tools import *