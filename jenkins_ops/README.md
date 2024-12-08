# Jenkins Operations Module for Kubiya

This module provides automated Jenkins job discovery and execution capabilities through Kubiya tools. It automatically syncs with your Jenkins server to create tools for each job, making Jenkins operations accessible through Kubiya.

## Features

- 🔄 Automatic Jenkins job discovery
- 🛠️ Dynamic tool generation for each job
- 📝 Support for all Jenkins parameter types
- 📊 Real-time job monitoring and log streaming
- 🔐 Secure credential handling
- 📁 Support for folders and complex job structures
- 🌳 Multi-branch pipeline support
- ⚡ Long-running job handling

## Architecture

```mermaid
graph TB
subgraph Discovery["Discovery Phase"]
Config["Jenkins Config"]
Parser["Job Parser"]
Tools["Tool Generator"]
Config -->|"Load & Validate"| Parser
Parser -->|"Discover Jobs"| Tools
Tools -->|"Generate"| KubiyaTools["Kubiya Tools"]
end
subgraph Execution["Execution Phase"]
User["User"]
Tool["Jenkins Tool"]
Jenkins["Jenkins Server"]
User -->|"Request"| Tool
Tool -->|"Execute"| Jenkins
Jenkins -->|"Status/Logs"| Tool
Tool -->|"Results"| User
end
Discovery -.->|"Enables"| Execution
```

## Discovery

```mermaid
sequenceDiagram
participant K as Kubiya
participant P as Parser
participant J as Jenkins
participant T as Tool Registry
K->>P: Initialize Parser
P->>J: Connect to Jenkins
P->>J: Get All Jobs
J-->>P: Jobs List
loop For Each Job
P->>J: Get Job Config
J-->>P: Job XML Config
P->>P: Parse Parameters
P->>T: Create Tool
end
P-->>K: Tools Ready
```

## Execution of Jobs using Kubiya Tools

```mermaid
sequenceDiagram
participant U as User
participant K as Kubiya
participant T as Tool
participant J as Jenkins
U->>K: Request Job Run
K->>T: Validate Parameters
T->>J: Connect
T->>J: Queue Build
alt Long Running Job
loop Until Complete
T->>J: Check Status
J-->>T: Build Status
T-->>K: Progress Update
K-->>U: Status & Logs
end
else Regular Job
T->>J: Wait for Completion
J-->>T: Final Status
end
T-->>K: Build Results
K-->>U: Final Results
```

```mermaid
graph TD
A[Error Occurs] --> B{Error Type}
B -->|Connection| C[Connection Error]
B -->|Authentication| D[Auth Error]
B -->|Parameter| E[Parameter Error]
B -->|Execution| F[Job Error]
C --> G[Retry Connection]
D --> H[Check Credentials]
E --> I[Validate Input]
F --> J[Check Job Logs]
G --> K[Report Status]
H --> K
I --> K
J --> K
```

## Installation

```bash
pip install kubiya-jenkins-ops
```

```bash
export JENKINS_API_TOKEN="your-token"
export JENKINS_URL="your-jenkins-url"
```

```bash
cp jenkins_config.json.example jenkins_config.json
Edit the configuration file with your settings
```

```bash
git clone https://github.com/kubiya-sandbox/jenkins-ops.git
cd jenkins-ops
```

```bash
pip install -e .
```

```bash
python -m pytest tests/
```
