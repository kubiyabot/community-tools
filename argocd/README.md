# <img src="https://cncf-branding.netlify.app/img/projects/argo/icon/color/argo-icon-color.svg" width="70" align="center" /> ArgoCD Tools for Kubiya

<div align="center">

> 🚀 GitOps deployment automation with ArgoCD-powered tools

[![Kubiya Platform](https://img.shields.io/badge/Kubiya-Platform-blue?style=for-the-badge&logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAA4AAAAOCAYAAAAfSC3RAAAACXBIWXMAAAsTAAALEwEAmpwYAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAADASURBVHgBjZLBDcIwEARPCX/cAakg6YB0QEqgA6ACQgWEDkgHpAPoAFcAJUAFrGYtWbKwlGQ/Zn1n786SyZxzEfYKd4uphSunA1rX7dKAzlWQBqbB+bacc1m4wCtFg1GM4RQKLRQXeKNh4Vz/lWjBHw3X+2KmE0+oB+71M0UR1WOwHvzJ0sDgC9xh0lbOLNbk4kUBJXw8ITPU4N+rR7zQwOKXvNDgvP6GpgbOXIQRX+4ZlX4QBPbBxbpV/FV8ARfDSCg/4aaZAAAAAElFTkSuQmCC)](https://chat.kubiya.ai)
[![ArgoCD](https://img.shields.io/badge/ArgoCD-GitOps-EF7B4D?style=for-the-badge&logo=argo&logoColor=white)](https://argoproj.github.io/cd)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-Powered-326CE5?style=for-the-badge&logo=kubernetes&logoColor=white)](https://kubernetes.io)

</div>

## 🎯 Overview

This module provides a comprehensive suite of containerized tools for managing ArgoCD operations through Kubiya. Built on Docker containers and leveraging the power of the Kubiya platform, these tools enable GitOps-based deployment, monitoring, and management of your Kubernetes applications.

## 🏗️ How It Works

```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'primaryColor': '#EF7B4D', 'fontFamily': 'arial', 'fontSize': '16px' }}}%%
graph LR
    A([Kubiya<br/>Teammate]) -->|Command| B[ArgoCD API]
    B -->|Manage| C[Applications]
    B -->|Deploy| D[K8s Resources]
    B -->|Configure| E[Projects]
    
    style A fill:#EF7B4D,color:#fff,stroke-width:2px
    style B fill:#1a73e8,color:#fff,stroke-width:2px
    style C fill:#EF7B4D,color:#fff,stroke-width:2px
    style D fill:#EF7B4D,color:#fff,stroke-width:2px
    style E fill:#EF7B4D,color:#fff,stroke-width:2px
```

## ✨ Key Features

<table>
<tr>
<td width="50%">

### 📊 Application Management
- List all applications
- Get application details
- Synchronize applications
- Check sync status
- Create and delete applications

</td>
<td width="50%">

### 🔍 Project Management
- List all projects
- Get project details
- Create new projects
- Delete projects
- Manage project settings

</td>
</tr>
<tr>
<td width="50%">

### 🚀 Deployment Automation
- GitOps-based workflows
- Automated synchronization
- Version tracking
- Rollback capabilities

</td>
<td width="50%">

### 📡 Cluster Management
- Multi-cluster deployments
- Namespace management
- Resource tracking
- Health monitoring

</td>
</tr>
</table>

## 📋 Prerequisites

<table>
<tr>
<td width="120" align="center">
<img src="https://cncf-branding.netlify.app/img/projects/argo/icon/color/argo-icon-color.svg" width="50"/>
<br/>ArgoCD
</td>
<td>

- ArgoCD server
- API access token
- Appropriate permissions
- Running ArgoCD instance

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

### 1️⃣ Configure ArgoCD Connection

```bash
export ARGOCD_SERVER="https://argocd.example.com"
export ARGOCD_AUTH_TOKEN="your-auth-token"
```

### 2️⃣ Install Tools

1. Visit [chat.kubiya.ai](https://chat.kubiya.ai)
2. Navigate to teammate settings
3. Install ArgoCD tools source
4. Configure credentials

### 3️⃣ Start Using

Example commands:
```
"List all ArgoCD applications"
"Get details for application X"
"Sync application X"
"Create a new application from repository Y"
```

## 📚 Learn More

<table>
<tr>
<td width="33%" align="center">

[![Kubiya Docs](https://img.shields.io/badge/Kubiya-Docs-blue?style=for-the-badge&logo=readthedocs)](https://docs.kubiya.ai)

</td>
<td width="33%" align="center">

[![ArgoCD Docs](https://img.shields.io/badge/ArgoCD-Docs-EF7B4D?style=for-the-badge&logo=argo)](https://argo-cd.readthedocs.io/)

</td>
<td width="33%" align="center">

[![Community](https://img.shields.io/badge/Join-Community-orange?style=for-the-badge&logo=slack)](https://argoproj.github.io/community/)

</td>
</tr>
</table>

---

<div align="center">

Built with ❤️ by the [Kubiya Community](https://chat.kubiya.ai)

<img src="https://cncf-branding.netlify.app/img/projects/argo/icon/color/argo-icon-color.svg" width="40" />

</div> 