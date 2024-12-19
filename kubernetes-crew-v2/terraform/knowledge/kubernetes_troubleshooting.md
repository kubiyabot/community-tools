# Kubernetes Troubleshooting Guide

## Diagnostic Tools

### Error Detection
- Use `find_suspicious_errors_tool` for cluster issues
  ```yaml
  Parameters:
  - namespace: required ('all' for cluster-wide)
  ```

### Resource Investigation
- Use `get_resource_events_tool` for detailed events
  ```yaml
  Required Parameters:
  - resource_type: pod/deployment/etc
  - resource_name: name
  - namespace: required
  ```

### Log Analysis
- Use `get_resource_logs_tool` for debugging
  ```yaml
  Key Parameters:
  - resource_type: usually pod
  - resource_name: name
  - namespace: required
  - container: optional
  - previous: bool
  - tail: line count
  ```

## Common Issues & Solutions
1. Pod Crashes
   - Check logs with `get_resource_logs_tool`
   - Verify resource limits
   - Check image pull status

2. Scaling Issues
   - Use `check_replicas_tool`
   - Verify PDB with `pod_disruption_budget_checker_tool`
   - Check node resources

3. Network Problems
   - Use `network_policy_analyzer_tool`
   - Check service endpoints
   - Verify DNS resolution