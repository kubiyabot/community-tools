import os
import sys
from kubiya_sdk.tools.registry import tool_registry
from ..utils.script_runner import run_script
from ..kubewatch.builder import KubeWatchConfigBuilder

def initialize():
    """Initialize the Kubernetes tools environment."""
    try:
        # Get and parse configuration
        config = tool_registry.dynamic_config
        settings = KubeWatchConfigBuilder.parse_config(config)
        
        # Generate base configuration
        config_content = f"""
version: "1"
filter:
  watch_for: []
  settings:
    dedup_interval: {settings.numeric_settings['dedup_window']}
    include_labels: true
    namespace_isolation: {str(settings.advanced_settings['namespace_isolation']).lower()}
    group_by:
      - owner
      - app_label
    log_tail: {settings.numeric_settings['max_log_lines']}
handler:
  webhook:
    url: "{settings.webhook_url}"
    batchSize: {settings.numeric_settings['batch_size']}
    maxWaitTime: "{settings.numeric_settings['max_wait_time']}"
    minWaitTime: "{settings.numeric_settings['min_wait_time']}"
    groupEvents: {str(settings.advanced_settings['group_events']).lower()}
    groupBy:
      - kind
      - namespace
      - reason
      - owner
    filtering:
      includeRoutineEvents: false
      minSeverity: "{settings.advanced_settings['min_severity']}"
      deduplication:
        enabled: true
        window: "{settings.numeric_settings['dedup_window']}"
resource:
  pod: {str(settings.watch_settings['watch_pod']).lower()}
  node: {str(settings.watch_settings['watch_node']).lower()}
  deployment: {str(settings.watch_settings['watch_deployment']).lower()}
  service: {str(settings.watch_settings['watch_service']).lower()}
  ingress: {str(settings.watch_settings['watch_ingress']).lower()}
  event: {str(settings.watch_settings['watch_event']).lower()}
enrichment:
  include_logs: {str(settings.advanced_settings['include_logs']).lower()}
  include_events: {str(settings.advanced_settings['include_events']).lower()}
  include_metrics: {str(settings.advanced_settings['include_metrics']).lower()}
  max_log_lines: {settings.numeric_settings['max_log_lines']}
  max_events: {settings.numeric_settings['max_events']}
"""
        
        # Write configuration
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'kubewatch.yaml')
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        with open(config_path, 'w') as f:
            f.write(config_content)
        
        # Handle webhook URL and apply configuration
        if settings.webhook_url:
            os.environ['KUBIYA_KUBEWATCH_WEBHOOK_URL'] = settings.webhook_url
            print("🔗 Webhook URL configured")
            
            # Apply configuration using init_cluster.sh
            init_script = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'utils', 'init_cluster.sh')
            run_script(f"bash {init_script}")
        else:
            print("⚠️  No webhook URL provided - notifications will not be sent")
            if 'KUBIYA_KUBEWATCH_WEBHOOK_URL' in os.environ:
                del os.environ['KUBIYA_KUBEWATCH_WEBHOOK_URL']
        
        # Print status
        print("✅ Kubernetes tools initialized successfully")
        print(f"📝 KubeWatch configuration written to: {config_path}")
        print(f"🔍 Monitoring namespaces: {', '.join(settings.namespaces)}")
        print("🎯 Watching for:")
        if settings.watch_settings['watch_pod']: print("  • Pod issues")
        if settings.watch_settings['watch_node']: print("  • Node issues")
        if settings.watch_settings['watch_event']: print("  • Events")
        
    except Exception as e:
        print(f"❌ Initialization failed: {str(e)}", file=sys.stderr)
        sys.exit(1)

__all__ = ['initialize'] 