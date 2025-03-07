# <img src="https://user-images.githubusercontent.com/113339427/211711571-a01471d5-5405-4876-a129-af0ce48dd2c4.svg" width="70" align="center" /> PagerDuty Tools for Kubiya

<div align="center">

> 🚨 Streamline your incident management with Kubiya-powered PagerDuty automation

[![Kubiya Platform](https://img.shields.io/badge/Kubiya-Platform-blue?style=for-the-badge)](https://chat.kubiya.ai)
[![PagerDuty](https://img.shields.io/badge/PagerDuty-Managed-green?style=for-the-badge&logo=pagerduty)](https://pagerduty.com)

</div>

## 🎯 Overview

This module provides tools for managing PagerDuty incidents through Kubiya. Built on Docker containers and leveraging the PagerDuty API, these tools enable seamless incident management automation.

## 🏗️ How It Works

```mermaid
graph LR
    A([Kubiya<br/>Teammate]) -->|Execute| B[PagerDuty<br/>Tools]
    B -->|API| C[PagerDuty<br/>Instance]
    C -->|Manage| D{Incidents &<br/>Services}
    
    style A fill:#6f42c1,color:#fff
    style B fill:#1a73e8,color:#fff
    style C fill:#25C151,color:#fff
    style D fill:#34a853,color:#fff
```

## ✨ Key Features

- Incident Creation
- Incident Management
- Status Updates
- Service Integration

## 📋 Prerequisites

- PagerDuty account
- PagerDuty API key
- Service ID configured
- Kubiya teammate configured

## 🚀 Quick Start

1. **Install Tool Source**
   ```bash
   # Through Kubiya Platform
   1. Visit chat.kubiya.ai
   2. Navigate to teammate settings
   3. Add PagerDuty tools source
   ```

2. **Configure Environment**
   ```bash
   # Required environment variables
   PD_API_KEY=your-pagerduty-api-key
   SERVICE_ID=your-service-id
   ```

3. **Start Using**
   ```bash
   # Example commands in Kubiya chat
   "Create a new incident"
   "List all incidents"
   "Update incident status"
   ```

## 📚 Documentation

For detailed documentation, visit [docs.kubiya.ai](https://docs.kubiya.ai)

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) for details.

---

<div align="center">

Built with ❤️ by the [Kubiya Community](https://chat.kubiya.ai)

</div> 