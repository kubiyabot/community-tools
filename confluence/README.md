# <img src="https://cdn.worldvectorlogo.com/logos/confluence-1.svg" width="70" align="center" /> Confluence Tools for Kubiya

<div align="center">

> 📚 Access and manage your Confluence knowledge base with Kubiya automation

[![Kubiya Platform](https://img.shields.io/badge/Kubiya-Platform-blue?style=for-the-badge&logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAA4AAAAOCAYAAAAfSC3RAAAACXBIWXMAAAsTAAALEwEAmpwYAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAADASURBVHgBjZLBDcIwEARPCX/cAakg6YB0QEqgA6ACQgWEDkgHpAPoAFcAJUAFrGYtWbKwlGQ/Zn1n786SyZxzEfYKd4uphSunA1rX7dKAzlWQBqbB+bacc1m4wCtFg1GM4RQKLRQXeKNh4Vz/lWjBHw3X+2KmE0+oB+71M0UR1WOwHvzJ0sDgC9xh0lbOLNbk4kUBJXw8ITPU4N+rR7zQwOKXvNDgvP6GpgbOXIQRX+4ZlX4QBPbBxbpV/FV8ARfDSCg/4aaZAAAAAElFTkSuQmCC)](https://chat.kubiya.ai)
[![Confluence](https://img.shields.io/badge/Confluence-Powered-0052CC?style=for-the-badge&logo=confluence&logoColor=white)](https://www.atlassian.com/software/confluence)
[![Docker](https://img.shields.io/badge/Docker-Powered-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com)

</div>

## 🎯 Overview

This module provides a comprehensive suite of containerized tools for accessing and managing Confluence content through Kubiya. Built on Docker containers and leveraging the power of the Kubiya platform, these tools enable seamless integration with your organization's knowledge base.

## 🏗️ How It Works

```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'primaryColor': '#0052CC', 'fontFamily': 'arial', 'fontSize': '16px' }}}%%
graph LR
    A([Kubiya<br/>Teammate]) -->|Query| B[Confluence API]
    B -->|Fetch| C[Pages]
    B -->|Search| D[Content]
    B -->|Access| E[Spaces]
    
    style A fill:#0052CC,color:#fff,stroke-width:2px
    style B fill:#1a73e8,color:#fff,stroke-width:2px
    style C fill:#0052CC,color:#fff,stroke-width:2px
    style D fill:#0052CC,color:#fff,stroke-width:2px
    style E fill:#0052CC,color:#fff,stroke-width:2px
```

## ✨ Key Features

<table>
<tr>
<td width="50%">

### 📄 Page Access
- Read page content
- Extract page metadata
- Access page history
- View page attachments

</td>
<td width="50%">

### 🔍 Content Search
- Full-text search
- Space-specific queries
- Label-based filtering
- Content categorization

</td>
</tr>
<tr>
<td width="50%">

### 🏢 Space Management
- List available spaces
- Space content overview
- Permission information
- Space statistics

</td>
<td width="50%">

### 📊 Content Analysis
- Extract structured data
- Generate summaries
- Content relationships
- Knowledge mapping

</td>
</tr>
</table>

## 📋 Prerequisites

<table>
<tr>
<td width="120" align="center">
<img src="https://cdn.worldvectorlogo.com/logos/confluence-1.svg" width="50"/>
<br/>Confluence
</td>
<td>

- Confluence Cloud or Server instance
- API token or credentials
- Appropriate permissions
- Space and page access

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

### 1️⃣ Configure Confluence Connection

```bash
export CONFLUENCE_URL="https://your-domain.atlassian.net/wiki"
export CONFLUENCE_API_TOKEN="your-api-token"
export CONFLUENCE_USERNAME="your-email@example.com"
```

### 2️⃣ Install Tools

1. Visit [chat.kubiya.ai](https://chat.kubiya.ai)
2. Navigate to teammate settings
3. Install Confluence tools source
4. Configure credentials

### 3️⃣ Start Using

Example commands:
```
"Get content from page X"
"Search for information about Y in space Z"
"List all spaces I have access to"
"Summarize the content in page ABC"
```

## 📚 Learn More

<table>
<tr>
<td width="33%" align="center">

[![Kubiya Docs](https://img.shields.io/badge/Kubiya-Docs-blue?style=for-the-badge&logo=readthedocs)](https://docs.kubiya.ai)

</td>
<td width="33%" align="center">

[![Confluence Docs](https://img.shields.io/badge/Confluence-Docs-0052CC?style=for-the-badge&logo=confluence)](https://developer.atlassian.com/cloud/confluence/rest/v1/intro/)

</td>
<td width="33%" align="center">

[![Community](https://img.shields.io/badge/Join-Community-orange?style=for-the-badge&logo=slack)](https://community.atlassian.com/)

</td>
</tr>
</table>

---

<div align="center">

Built with ❤️ by the [Kubiya Community](https://chat.kubiya.ai)

<img src="https://cdn.worldvectorlogo.com/logos/confluence-1.svg" width="40" />

</div> 