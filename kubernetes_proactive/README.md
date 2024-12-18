# Kubernetes Tools Module for Kubiya SDK

## Dynamic Configuration

The Kubernetes Tools module supports dynamic configuration through the Kubiya SDK's dynamic configuration system. Here are the available configuration options:

### Required Settings
- `webhook_url`: Webhook URL for KubeWatch notifications (optional - if not provided, notifications will not be sent)

### Namespace Configuration
- `namespaces`: Comma-separated list of namespaces to monitor (default: "default,kube-system")

### Watch Settings
- `watch_event`: Monitor Kubernetes events (default: true)
- `watch_node`: Monitor node status (default: true)
- `watch_pod`: Monitor pod status (default: true)
- `watch_deployment`: Monitor deployments (default: true)
- `watch_service`: Monitor services (default: false)
- `watch_ingress`: Monitor ingress resources (default: false)
- `watch_configmap`: Monitor configmaps (default: false)
- `watch_secret`: Monitor secrets (default: false)
- `watch_job`: Monitor jobs and cronjobs (default: true)

### Performance Settings
- `batch_size`: Number of events to batch before sending (default: 5)
- `max_wait_time`: Maximum time to wait before sending batch (default: "30s")
- `min_wait_time`: Minimum time between batches (default: "5s")
- `dedup_window`: Time window for deduplication (default: "15m")
- `max_log_lines`: Maximum number of log lines to include (default: 50)
- `max_events`: Maximum number of events to include (default: 10)

### Advanced Settings
- `include_logs`: Include container logs in notifications (default: true)
- `include_events`: Include related events in notifications (default: true)
- `include_metrics`: Include resource metrics in notifications (default: true)
- `namespace_isolation`: Isolate events by namespace (default: false)
- `min_severity`: Minimum severity level to report (default: "Warning")
- `group_events`: Group related events together (default: true)

### Example Configurations

1. With Webhook (Full Monitoring):
```yaml
dynamic_config:
  webhook_url: "https://webhooksource-kubiya.hooks.kubiya.ai:8443/webhook"
  namespaces: "default,kube-system,production"
  watch_pod: true
  watch_node: true
  watch_deployment: true
```

2. Without Webhook (Monitoring Only):
```yaml
dynamic_config:
  namespaces: "default,kube-system"
  watch_pod: true
  watch_node: true
  include_logs: true
```

### Behavior
- If webhook_url is provided: Full monitoring with notifications
- If webhook_url is not provided: 
  - Configuration will be generated but not applied
  - No notifications will be sent
  - Monitoring can still be used for local inspection

### KubeWatch Integration

The module automatically configures KubeWatch based on your dynamic configuration settings. It will:

1. Generate appropriate KubeWatch configuration
2. Apply the configuration to your cluster
3. Monitor specified resources and namespaces
4. Send notifications via webhook for important events

### Notification Format

Events are formatted with rich context and emojis for better readability:

```
🚨 Critical Pod Issue Detected
═══════════════════════════
Pod: example-pod
Namespace: default
Status: Failed
Issue: CrashLoopBackOff

Details:
• State: Waiting
• Restarts: 5
• Exit Code: 1
• Message: "Container failed to start"

Context:
• Owner: Deployment/example-app
• Related Events: 3
```

## Usage Examples

```python
# Example: Configure monitoring for specific namespaces
tool_registry.dynamic_config = {
    'webhook_url': 'https://your-webhook-url',
    'namespaces': 'production,staging',
    'watch_pod': True,
    'watch_deployment': True,
    'include_logs': True,
    'max_log_lines': 100
}

# The module will automatically configure KubeWatch with these settings
```

## Error Handling

The module performs validation of all configuration settings and will raise clear error messages if:
- Required settings are missing
- Values are invalid
- Configuration cannot be applied

## Best Practices

1. Start with minimal monitoring (pods and deployments)
2. Adjust batch settings based on event volume
3. Use namespace isolation in large clusters
4. Set appropriate severity levels for your environment
5. Configure log line limits based on application verbosity
