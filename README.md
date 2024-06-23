 
![Kubiya](https://avatars.githubusercontent.com/u/87862858?s=200&v=4)
# Kubiya's Community Tools


## Table of Contents

- [Introduction](#introduction)
- [Prerequisites](#prerequisites)
- [Getting Started](#getting-started)
    - [Building the Docker Image](#building-the-docker-image)
    - [Running the Container](#running-the-container)
- [Configuration](#configuration)
    - [Dockerfile](#dockerfile)
    - [entry.sh Script](#entrysh-script)
    - [Tools Installed](#tools-installed)
    - [Customizing the Agent](#customizing-the-agent)
- [Contributing](#contributing)
- [License](#license)

## Introduction
Kubiya's Comuunity Tools are set of tools that can be used by the [Kubiya Agent](https://docs.kubiya.ai/gen-2-docs/agents-experimental). 
The tools can then be used by the agent, using natural language and without the need to provide the Agent any instructions on when and how to use the tool, through the power of LLM and AI.

It can also replace the need of creating [custom Kubiya Agents](https://docs.kubiya.ai/gen-2-docs/agents-experimental) by providing the agent's enviorment with variours tools, docker images and cli's that the agent can then execute at run time.


# Schema

### Common Fields

- **name**: The name of the tool.
- **description**: A brief description of what the tool does.
- **type**: The type of the tool (e.g., bash, python, docker).
- **content**: The script or command that the tool runs.
- **content_url**: URL to the content if hosted externally.
- **args**: Arguments that the tool accepts.
- **env**: Environment variables required by the tool.
- **dependencies**: Dependencies required by the tool.
- **dependencies_url**: URL to the dependencies if hosted externally.
- **openapi**: OpenAPI specification for the tool.
- **files**: Files to be used with the tool.
- **services**: Services required by the tool.
- **git_repo**: Git repository to be used with the tool.
- **volumes**: Volumes that the tool mounts.
- **icon_url**: URL to the icon for the tool.
- **image**: Docker image to be used by the tool.
- **long_running**: Indicates if the tool is long-running.
- **on_start**: Script to run on start.
- **on_complete**: Script to run on completion.

### Example Configurations

#### 1. Databricks CLI Tool

This tool allows you to run Databricks CLI commands. It ensures the Databricks CLI is installed and properly configured before executing any command.

```
tools:
  - name: databricks_cli
    description: Run Databricks CLI commands
    type: bash
    alias: databricks
    content: |
      #!/bin/bash
      set -e
      # Make sure databricks CLI is installed
      if ! command -v databricks &> /dev/null
      then
          # Install databricks CLI
          apk update && \
          apk upgrade && \
          apk add curl
          curl -fsSL https://raw.githubusercontent.com/databricks/setup-cli/main/install.sh | sh
      fi

      # Run the Databricks CLI command
      databricks $@
    args:
      command:
        description: 'The Databricks CLI command to run (example: databricks workspace ls)'
        required: true
    env:
      - "DATABRICKS_TOKEN"
      - "DATABRICKS_HOST"
    volumes:
      - path: /workspace
        name: databricks-workspace
2. Python Script Tool
This tool runs a Python script with specified arguments and environment variables.
```

```
tools:
  - name: python_script_tool
    description: Run a Python script
    type: python
    alias: pyscript
    content: |
      import sys
      print(f"Running Python script with args: {sys.argv[1:]}")
    args:
      script_args:
        description: 'Arguments to pass to the Python script'
        required: false
    env:
      - "PYTHON_ENV"
3. Docker Container Tool
This tool runs a Docker container with specified environment variables and volumes.
```

```
tools:
  - name: docker_tool
    description: Run a Docker container
    type: docker
    alias: dockertool
    image: "ubuntu:latest"
    content: |
      #!/bin/bash
      echo "Running Docker container with environment variables:"
      env
    env:
      - "DOCKER_ENV"
    volumes:
      - path: /data
        name: docker-data
4. Tool with External Content and Dependencies
This tool fetches its script and dependencies from external URLs.
```

```
tools:
  - name: external_content_tool
    description: Tool with external content and dependencies
    type: bash
    alias: exttool
    content_url: "https://example.com/script.sh"
    dependencies_url: "https://example.com/dependencies.tar.gz"
    args:
      command:
        description: 'Command to run'
        required: true
    env:
      - "EXTERNAL_TOOL_ENV"
5. Tool with OpenAPI Specification
This tool uses an OpenAPI specification for its configuration.
```

```
tools:
  - name: openapi_tool
    description: Tool with OpenAPI specification
    type: bash
    alias: apitool
    openapi:
      url: "https://example.com/openapi.yaml"
    content: |
      #!/bin/bash
      echo "Running tool with OpenAPI specification"
    args:
      api_command:
        description: 'API command to run'
        required: true
    env:
      - "OPENAPI_TOOL_ENV"
6. Tool with File and Service Specifications
This tool includes files and services required for its operation.
```

```
tools:
  - name: file_service_tool
    description: Tool with file and service specifications
    type: bash
    alias: fileservicetool
    content: |
      #!/bin/bash
      echo "Running tool with files and services"
    files:
      - source: "/local/path/to/file.txt"
        destination: "/container/path/to/file.txt"
        content: "File content"
    services:
      - image: "redis:latest"
        env:
          REDIS_PASSWORD: "password"
        exposed_port: 6379
7. Tool with Git Repository
This tool clones a Git repository and runs a script from it.
```

```
tools:
  - name: git_repo_tool
    description: Tool with Git repository
    type: bash
    alias: gittool
    content: |
      #!/bin/bash
      git clone https://github.com/example/repo.git /workspace/repo
      cd /workspace/repo
      ./run_script.sh
    git_repo:
      url: "https://github.com/example/repo.git"
      branch: "main"
      dir: "/workspace/repo"
    volumes:
      - path: /workspace
        name: git-repo-workspace
```
