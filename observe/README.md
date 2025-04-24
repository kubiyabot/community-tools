# <img src="https://cdn.worldvectorlogo.com/logos/observe.svg" width="70" align="center" /> Observe Tools for Kubiya

<div align="center">

> 🔍 Monitor and analyze your infrastructure with Observe-powered automation

[![Kubiya Platform](https://img.shields.io/badge/Kubiya-Platform-blue?style=for-the-badge&logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAA4AAAAOCAYAAAAfSC3RAAAACXBIWXMAAAsTAAALEwEAmpwYAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAADASURBVHgBjZLBDcIwEARPCX/cAakg6YB0QEqgA6ACQgWEDkgHpAPoAFcAJUAFrGYtWbKwlGQ/Zn1n786SyZxzEfYKd4uphSunA1rX7dKAzlWQBqbB+bacc1m4wCtFg1GM4RQKLRQXeKNh4Vz/lWjBHw3X+2KmE0+oB+71M0UR1WOwHvzJ0sDgC9xh0lbOLNbk4kUBJXw8ITPU4N+rR7zQwOKXvNDgvP6GpgbOXIQRX+4ZlX4QBPbBxbpV/FV8ARfDSCg/4aaZAAAAAElFTkSuQmCC)](https://chat.kubiya.ai)
[![Observe](https://img.shields.io/badge/Observe-Monitored-632CA6?style=for-the-badge&logo=observe&logoColor=white)](https://www.observe.com/)
[![Docker](https://img.shields.io/badge/Docker-Powered-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com)

</div>

## 🎯 Overview

This module provides a comprehensive suite of containerized tools for managing Observe operations through Kubiya. Built on Docker containers and leveraging the power of the Kubiya platform, these tools enable seamless monitoring, analysis, and troubleshooting of your infrastructure using the Observe observability platform.

## 🏗️ How It Works

```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'primaryColor': '#632CA6', 'fontFamily': 'arial', 'fontSize': '16px' }}}%%
graph LR
    A([Kubiya<br/>Teammate]) -->|Query| B[Observe API]
    B -->|Fetch| C[Metrics]
    B -->|Analyze| D[Logs]
    B -->|Monitor| E[Alerts]
    
    style A fill:#632CA6,color:#fff,stroke-width:2px
    style B fill:#1a73e8,color:#fff,stroke-width:2px
    style C fill:#632CA6,color:#fff,stroke-width:2px
    style D fill:#632CA6,color:#fff,stroke-width:2px
    style E fill:#632CA6,color:#fff,stroke-width:2px
```

## ✨ Available Tools

<table>
<tr>
<td width="50%">

### 📊 Observe Query Metrics
Retrieve metrics and insights from Observe datasets using OPAL queries.

**Key Parameters:**
- Dataset ID
- OPAL Query
- Time Range
- Formatting Options

</td>
<td width="50%">

### 🔍 Observe Fetch Logs
Fetch log data from Observe datasets with filtering capabilities.

**Key Parameters:**
- Dataset ID
- Time Range
- Filter Expression
- Result Limit

</td>
</tr>
<tr>
<td width="50%">

### 🚨 Observe Alert Details
Get comprehensive information about alerts and their associated monitors.

**Key Parameters:**
- Alert ID
- Optional Monitor Details

</td>
<td width="50%">

### 📈 Coming Soon
More tools are in development, including:
- Monitor Management
- Dataset Discovery
- Dashboard Integration
- Event Correlation

</td>
</tr>
</table>

## 📋 Prerequisites

<table>
<tr>
<td width="120" align="center">
<img src="https://cdn.worldvectorlogo.com/logos/observe.svg" width="50"/>
<br/>Observe
</td>
<td>

- Observe account
- API token
- Customer ID
- Dataset access permissions

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
- Network connectivity to Observe API

</td>
</tr>
</table>

## 🚀 Quick Start

### 1️⃣ Configure Observe Connection

```bash
export OBSERVE_API_KEY="your-api-token"
export OBSERVE_CUSTOMER_ID="your-customer-id"
```

### 2️⃣ Install Tools

1. Visit [chat.kubiya.ai](https://chat.kubiya.ai)
2. Navigate to teammate settings
3. Install Observe tools source
4. Configure credentials

### 3️⃣ Start Using

Example commands:
```
"Fetch logs from dataset 12345"
"Query metrics for CPU usage in the last 24 hours"
"Get details for alert 98765"
"Show error logs with filter status=error"
```

## 🔧 Tool Usage Examples

### Query Metrics
```
observe_query_metrics dataset_id=12345 query="events | where pod_name = 'api-server' | summarize count() by time(5m)"
```

### Fetch Logs
```
observe_fetch_logs dataset_id=12345 filter="severity='error' and service='payment-api'"
```

### Get Alert Details
```
observe_alert_details alert_id=98765
```

## 📚 Learn More

<table>
<tr>
<td width="33%" align="center">

[![Kubiya Docs](https://img.shields.io/badge/Kubiya-Docs-blue?style=for-the-badge&logo=readthedocs)](https://docs.kubiya.ai)

</td>
<td width="33%" align="center">

[![Observe Docs](https://img.shields.io/badge/Observe-Docs-632CA6?style=for-the-badge&logo=observe)](https://docs.observe.com/)

</td>
<td width="33%" align="center">

[![Community](https://img.shields.io/badge/Join-Community-orange?style=for-the-badge&logo=slack)](https://observe.slack.com)

</td>
</tr>
</table>

---

<div align="center">

Built with ❤️ by the [Kubiya Community](https://chat.kubiya.ai)

<img src="https://cdn.worldvectorlogo.com/logos/observe.svg" width="40" />

</div> 