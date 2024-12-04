# Kubernetes Management Prompts 🚀

## Deployment & Configuration 📦
> Common operations for deploying and configuring services

- "@Kubi Deploy nginx with 3 replicas and expose it on port 90. Please call this deployment 'delete-me-later' "
- "@Kubi Create a web deployment with health checks and resource limits, share configuration"
- "@Kubi Deploy Redis in default namespace: Create a Redis deployment (image: redis:latest) with 1 replica, memory limit 1Gi, CPU limit 500m, readiness probe on port 6379, and persistence enabled. For storage, create a 10GB persistent volume and corresponding PVC mounted at /data. Expose Redis as a service on port 6379, and display the connection string. Instead of creating yaml files for this setup you must do everything imparatively using kubectl."
- "@Kubi Set up MySQL database with secrets and show deployment status in the default namespace. First create the necessary secrets for MySQL root and user credentials, then deploy MySQL using those secrets and configure persistent storage. Finally, show me the deployment status including pod health, secret verification, and service endpoints."

## Monitoring & Health Checks 📊
> Monitor cluster and application health

- "@Kubi Check health of all production services and provide summary"
- "@Kubi Identify top 5 pods by memory usage"
- "@Kubi Monitor API deployment errors in the last hour"
- "@Kubi Audit services for high availability compliance"
- "@Kubi Report on unhealthy pods with log analysis"

## Scaling & Updates 🔄
> Manage application scaling and updates

- "@Kubi Configure CPU-based autoscaling for frontend service"
- "@Kubi Implement zero-downtime rolling update for backend service"
- "@Kubi Scale payment service to 5 replicas with health verification"
- "@Kubi Set up horizontal scaling for cache service"

## Architecture & Visualization 📐
> Create visual documentation of system architecture

- "@Kubi Generate frontend-to-backend service communication diagram"
- "@Kubi Create deployment pipeline visualization"
- "@Kubi Map service dependency relationships"
- "@Kubi Design network flow diagram for core services"

## Troubleshooting & Diagnostics 🔍
> Debug and resolve cluster issues

- "@Kubi Investigate payment-service pod restarts"
- "@Kubi Analyze failed or pending pods"
- "@Kubi Review API service logs for recent errors"
- "@Kubi Audit staging namespace configuration"

## Security & Compliance 🔒
> Security auditing and enforcement

- "@Kubi Identify pods running with root privileges"
- "@Kubi Audit services for TLS compliance"
- "@Kubi Review secret encryption status"
- "@Kubi Validate network policy implementation"

## Storage Management 💾
> Monitor and manage cluster storage

- "@Kubi Generate persistent volume usage report"
- "@Kubi Monitor volume capacity thresholds"
- "@Kubi Verify database backup status"
- "@Kubi Audit storage class configurations"

## High Availability 🔁
> Ensure service reliability

- "@Kubi Configure pod restart policies"
- "@Kubi Implement web service health checks"
- "@Kubi Set up API service liveness probes"
- "@Kubi Deploy database readiness checks"

## Network Configuration 🌐
> Manage cluster networking

- "@Kubi Create and verify web-app ingress rules"
- "@Kubi Configure microservice service discovery"
- "@Kubi Set up frontend load balancing"
- "@Kubi Audit internal service exposure"

## Maintenance Operations 🛠
> Regular cluster maintenance tasks

- "@Kubi Clean up expired jobs"
- "@Kubi Rotate and update database credentials"
- "@Kubi Update and verify ingress configurations"
- "@Kubi Check for deprecated API usage"
