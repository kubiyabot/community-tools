# Kubernetes Security Guide

## Security Tools & Operations

### Network Security
- Use `network_policy_analyzer_tool` for policy analysis
- Check exposed services and policy gaps
- Monitor ingress configurations

### Resource Access
- Use `pod_disruption_budget_checker_tool` for availability
  ```yaml
  Parameters:
  - namespace: optional, filters results
  ```

### Monitoring & Alerts
- Use `find_suspicious_errors_tool` for security events
  ```yaml
  Required Parameters:
  - namespace: specific or 'all'
  ```

## Security Best Practices
1. Enable network policies by default
2. Monitor pod security contexts
3. Regular security event checks
4. Implement resource quotas
5. Use RBAC for access control