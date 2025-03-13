# <img src="https://cdn.worldvectorlogo.com/logos/datadog.svg" width="70" align="center" /> Datadog Tools for Kubiya

<div align="center">

> 🔍 Monitor and analyze your infrastructure with Datadog-powered automation

[![Kubiya Platform](https://img.shields.io/badge/Kubiya-Platform-blue?style=for-the-badge&logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAA4AAAAOCAYAAAAfSC3RAAAACXBIWXMAAAsTAAALEwEAmpwYAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAADASURBVHgBjZLBDcIwEARPCX/cAakg6YB0QEqgA6ACQgWEDkgHpAPoAFcAJUAFrGYtWbKwlGQ/Zn1n786SyZxzEfYKd4uphSunA1rX7dKAzlWQBqbB+bacc1m4wCtFg1GM4RQKLRQXeKNh4Vz/lWjBHw3X+2KmE0+oB+71M0UR1WOwHvzJ0sDgC9xh0lbOLNbk4kUBJXw8ITPU4N+rR7zQwOKXvNDgvP6GpgbOXIQRX+4ZlX4QBPbBxbpV/FV8ARfDSCg/4aaZAAAAAElFTkSuQmCC)](https://chat.kubiya.ai)
[![Datadog](https://img.shields.io/badge/Datadog-Monitored-632CA6?style=for-the-badge&logo=datadog&logoColor=white)](https://www.datadoghq.com/)
[![Docker](https://img.shields.io/badge/Docker-Powered-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com)

</div>

## 🎯 Overview

This module provides a comprehensive suite of containerized tools for managing Datadog operations through Kubiya. Built on Docker containers and leveraging the power of the Kubiya platform, these tools enable seamless monitoring, analysis, and troubleshooting of your infrastructure.

## 🏗️ How It Works

```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'primaryColor': '#632CA6', 'fontFamily': 'arial', 'fontSize': '16px' }}}%%
graph LR
    A([Kubiya<br/>Teammate]) -->|Query| B[Datadog API]
    B -->|Fetch| C[Metrics]
    B -->|Analyze| D[Logs]
    B -->|Monitor| E[Alerts]
    
    style A fill:#632CA6,color:#fff,stroke-width:2px
    style B fill:#1a73e8,color:#fff,stroke-width:2px
    style C fill:#632CA6,color:#fff,stroke-width:2px
    style D fill:#632CA6,color:#fff,stroke-width:2px
    style E fill:#632CA6,color:#fff,stroke-width:2px
```

## ✨ Key Features

<table>
<tr>
<td width="50%">

### 📊 Metrics Analysis
- Key metric tracking
- Trend analysis
- Performance monitoring
- Resource utilization

</td>
<td width="50%">

### 🔍 Log Management
- Log querying
- Error analysis
- Pattern detection
- Historical data search

</td>
</tr>
<tr>
<td width="50%">

### 🚨 Alert Management
- Alert status tracking
- Incident investigation
- Alert history analysis
- Custom alert rules

</td>
<td width="50%">

### 📈 Trend Analysis
- Error rate comparison
- Performance trending
- Capacity planning
- Anomaly detection

</td>
</tr>
</table>

## 📋 Prerequisites

<table>
<tr>
<td width="120" align="center">
<img src="https://cdn.worldvectorlogo.com/logos/datadog.svg" width="50"/>
<br/>Datadog
</td>
<td>

- Datadog account
- API/Application keys
- Appropriate permissions
- Service enabled metrics

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

### 1️⃣ Configure Datadog Connection

```bash
export DD_API_KEY="your-api-key"
export DD_APP_KEY="your-application-key"
export DD_SITE="datadoghq.com"
```

### 2️⃣ Install Tools

1. Visit [chat.kubiya.ai](https://chat.kubiya.ai)
2. Navigate to teammate settings
3. Install Datadog tools source
4. Configure credentials

### 3️⃣ Start Using

Example commands:
```
"Get alert details for incident X"
"Compare error rates with last week"
"Query logs for service Y"
"Show key metrics for application Z"
```

## 📚 Learn More

<table>
<tr>
<td width="33%" align="center">

[![Kubiya Docs](https://img.shields.io/badge/Kubiya-Docs-blue?style=for-the-badge&logo=readthedocs)](https://docs.kubiya.ai)

</td>
<td width="33%" align="center">

[![Datadog Docs](https://img.shields.io/badge/Datadog-Docs-632CA6?style=for-the-badge&logo=datadog)](https://docs.datadoghq.com/)

</td>
<td width="33%" align="center">

[![Community](https://img.shields.io/badge/Join-Community-orange?style=for-the-badge&logo=slack)](https://datadoghq.slack.com)

</td>
</tr>
</table>

---

<div align="center">

Built with ❤️ by the [Kubiya Community](https://chat.kubiya.ai)

<img src="https://cdn.worldvectorlogo.com/logos/datadog.svg" width="40" />

</div> 