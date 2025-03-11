# <img src="https://www.jenkins.io/images/logos/jenkins/jenkins.png" width="70" align="center" /> Jenkins Tools for Kubiya

<div align="center">

> 🔧 Streamline your Jenkins CI/CD operations with Kubiya-powered automation

[![Kubiya Platform](https://img.shields.io/badge/Kubiya-Platform-blue?style=for-the-badge&logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAA4AAAAOCAYAAAAfSC3RAAAACXBIWXMAAAsTAAALEwEAmpwYAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAADASURBVHgBjZLBDcIwEARPCX/cAakg6YB0QEqgA6ACQgWEDkgHpAPoAFcAJUAFrGYtWbKwlGQ/Zn1n786SyZxzEfYKd4uphSunA1rX7dKAzlWQBqbB+bacc1m4wCtFg1GM4RQKLRQXeKNh4Vz/lWjBHw3X+2KmE0+oB+71M0UR1WOwHvzJ0sDgC9xh0lbOLNbk4kUBJXw8ITPU4N+rR7zQwOKXvNDgvP6GpgbOXIQRX+4ZlX4QBPbBxbpV/FV8ARfDSCg/4aaZAAAAAElFTkSuQmCC)](https://chat.kubiya.ai)
[![Jenkins](https://img.shields.io/badge/Jenkins-Managed-D24939?style=for-the-badge&logo=jenkins&logoColor=white)](https://www.jenkins.io/)
[![Docker](https://img.shields.io/badge/Docker-Powered-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com)

</div>

## 🎯 Overview

This module provides a comprehensive suite of containerized tools for managing Jenkins operations through Kubiya. Built on Docker containers and leveraging the power of the Kubiya platform, these tools enable seamless investigation and management of Jenkins builds, logs, and configurations.

## 🏗️ How It Works

```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'primaryColor': '#D24939', 'fontFamily': 'arial', 'fontSize': '16px' }}}%%
graph LR
    A([Kubiya<br/>Teammate]) -->|Query| B[Jenkins API]
    B -->|Fetch| C[Build Logs]
    B -->|Analyze| D[Job Config]
    B -->|Examine| E[Artifacts]
    
    style A fill:#D24939,color:#fff,stroke-width:2px
    style B fill:#1a73e8,color:#fff,stroke-width:2px
    style C fill:#D24939,color:#fff,stroke-width:2px
    style D fill:#D24939,color:#fff,stroke-width:2px
    style E fill:#D24939,color:#fff,stroke-width:2px
```

## ✨ Key Features

<table>
<tr>
<td width="50%">

### 🔍 Build Analysis
- Failed build investigation
- Log analysis
- Root cause identification
- Build artifact inspection

</td>
<td width="50%">

### 📊 Job Management
- Job configuration review
- Build history tracking
- Pipeline visualization
- Resource utilization monitoring

</td>
</tr>
<tr>
<td width="50%">

### 🚨 Alert Management
- Build failure notifications
- Performance alerts
- Security warnings
- Custom alert rules

</td>
<td width="50%">

### 🛠️ Troubleshooting
- Automated diagnostics
- Common issue detection
- Fix suggestions
- Historical pattern analysis

</td>
</tr>
</table>

## 📋 Prerequisites

<table>
<tr>
<td width="120" align="center">
<img src="https://www.jenkins.io/images/logos/jenkins/jenkins.png" width="50"/>
<br/>Jenkins
</td>
<td>

- Jenkins server access
- API credentials
- Appropriate permissions
- Network connectivity

</td>
</tr>
<tr>
<td width="120" align="center">
<img src="https://www.docker.com/wp-content/uploads/2023/08/logo-guide-logos-1.svg" width="50"/>
<br/>Docker
</td>
<td>

- Docker runtime
- Container access
- Volume mounts
- Network access

</td>
</tr>
</table>

## 🚀 Quick Start

### 1️⃣ Configure Jenkins Connection

```bash
export JENKINS_URL="https://your-jenkins-server"
export JENKINS_USER="your-username"
export JENKINS_TOKEN="your-api-token"
```

### 2️⃣ Install Tools

1. Visit [chat.kubiya.ai](https://chat.kubiya.ai)
2. Navigate to teammate settings
3. Install Jenkins tools source
4. Configure credentials

### 3️⃣ Start Using

Example commands:
```
"Get failed build logs for job X build Y"
"Analyze build failure patterns"
"Check job configuration history"
"Investigate build artifacts"
```

## 📚 Learn More

<table>
<tr>
<td width="33%" align="center">

[![Kubiya Docs](https://img.shields.io/badge/Kubiya-Docs-blue?style=for-the-badge&logo=readthedocs)](https://docs.kubiya.ai)

</td>
<td width="33%" align="center">

[![Jenkins Docs](https://img.shields.io/badge/Jenkins-Docs-D24939?style=for-the-badge&logo=jenkins)](https://www.jenkins.io/doc/)

</td>
<td width="33%" align="center">

[![Community](https://img.shields.io/badge/Join-Community-orange?style=for-the-badge&logo=slack)](https://www.jenkins.io/participate/)

</td>
</tr>
</table>

---

<div align="center">

Built with ❤️ by the [Kubiya Community](https://chat.kubiya.ai)

<img src="https://www.jenkins.io/images/logos/jenkins/jenkins.png" width="40" />

</div> 