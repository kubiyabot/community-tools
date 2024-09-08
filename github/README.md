# GitHub Tools Module for Kubiya SDK

This module provides a comprehensive set of tools for interacting with GitHub using the GitHub CLI via the Kubiya SDK. These tools are designed to be stateless and easily discoverable by the Kubiya engine, allowing for dynamic execution in various environments with different GitHub configurations.

## Tools Overview

1. **Repo**: Manages GitHub repositories (create, clone, view, list, delete)
2. **Issue**: Manages GitHub issues (create, list, view, close, reopen)
3. **PR**: Manages GitHub pull requests (create, list, view, checkout, merge, close)
4. **Workflow**: Manages GitHub Actions workflows (list, view, run, disable, enable)
5. **Release**: Manages GitHub releases (create, list, view, delete)
6. **Gist**: Manages GitHub Gists
7. **Auth**: Handles GitHub authentication
8. **Search**: Performs GitHub searches

## Configuration

This module uses the GitHub CLI configuration stored in `~/.config/gh/config.yml` and `~/.config/gh/hosts.yml`. Make sure these files are properly configured with your GitHub authentication token.

The `GITHUB_TOKEN` environment variable is also used for authentication. Ensure it is set with a valid GitHub personal access token.

## Usage

To use these tools in your Kubiya SDK workflows, first add this module as a source in your Teammate Environment. Then, you can use the tools in your workflows like this:
