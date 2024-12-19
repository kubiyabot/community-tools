# Kubernetes Operations Guide

## Common Operations & Tool Mappings

### Pod Management
- Use `pod_management_tool` for basic pod operations
  ```yaml
  Key Parameters:
  - action: get, delete, logs
  - name: pod name
  - namespace: required
  - container: optional for logs
  ```

### Deployment Operations
- Use `deployment_management_tool` for lifecycle management
  ```yaml
  Key Parameters:
  - action: create, delete, get
  - name: deployment name
  - namespace: required
  - image: for create
  - replicas: for create
  ```

### Scaling Operations
- Use `change_replicas_tool` for manual scaling
  ```yaml
  Required Parameters:
  - resource_type: deployment/statefulset
  - resource_name: name
  - replicas: target count
  - namespace: required
  ```

### Resource Monitoring
- Use `resource_usage_tool` for usage metrics
  ```yaml
  Parameters:
  - resource_type: nodes/pods
  - namespace: optional for pods
  ```

### Health Checks
- Use `cluster_health_tool` for overall status
- Use `check_pod_restarts_tool` for stability issues
  ```yaml
  Parameters:
  - namespace: optional
  - threshold: default 5
  ```

## Best Practices
1. Always specify namespace for targeted operations
2. Use resource limits and requests
3. Implement health checks for all deployments
4. Monitor pod restart counts
5. Keep replica count aligned with load