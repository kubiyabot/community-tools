import os
import sys
import json
from kubiya_sdk.tools.registry import tool_registry
from ..utils.script_runner import run_script
from ..kubewatch.builder import KubeWatchConfigBuilder

def initialize():
    """Initialize the Kubernetes tools environment."""
    try:
        # Get and parse configuration
        config = tool_registry.dynamic_config
        settings = KubeWatchConfigBuilder.parse_config(config)
        
        # Generate KubeWatch configuration as a dictionary
        kubewatch_config = {
            "apiVersion": "v1",
            "kind": "ConfigMap",
            "metadata": {
                "name": "kubewatch-config",
                "namespace": "default"
            },
            "data": {
                ".kubewatch.yaml": {
                    "version": "1",
                    "filter": {
                        "watch_for": [],
                        "settings": {
                            "dedup_interval": settings.numeric_settings['dedup_window'],
                            "include_labels": True,
                            "namespace_isolation": settings.advanced_settings['namespace_isolation'],
                            "group_by": ["owner", "app_label"],
                            "log_tail": settings.numeric_settings['max_log_lines']
                        }
                    },
                    "handler": {
                        "webhook": {
                            "url": settings.webhook_url,
                            "batchSize": settings.numeric_settings['batch_size'],
                            "maxWaitTime": settings.numeric_settings['max_wait_time'],
                            "minWaitTime": settings.numeric_settings['min_wait_time'],
                            "groupEvents": settings.advanced_settings['group_events'],
                            "groupBy": ["kind", "namespace", "reason", "owner"],
                            "filtering": {
                                "includeRoutineEvents": False,
                                "minSeverity": settings.advanced_settings['min_severity'],
                                "deduplication": {
                                    "enabled": True,
                                    "window": settings.numeric_settings['dedup_window']
                                }
                            }
                        }
                    },
                    "resource": {
                        "pod": settings.watch_settings['watch_pod'],
                        "node": settings.watch_settings['watch_node'],
                        "deployment": settings.watch_settings['watch_deployment'],
                        "service": settings.watch_settings['watch_service'],
                        "ingress": settings.watch_settings['watch_ingress'],
                        "event": settings.watch_settings['watch_event']
                    },
                    "enrichment": {
                        "include_logs": settings.advanced_settings['include_logs'],
                        "include_events": settings.advanced_settings['include_events'],
                        "include_metrics": settings.advanced_settings['include_metrics'],
                        "max_log_lines": settings.numeric_settings['max_log_lines'],
                        "max_events": settings.numeric_settings['max_events']
                    }
                }
            }
        }
        
        # Write configuration as JSON
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'kubewatch.json')
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        with open(config_path, 'w') as f:
            json.dump(kubewatch_config, f, indent=2)
        
        # Handle webhook URL and apply configuration
        if settings.webhook_url:
            os.environ['KUBIYA_KUBEWATCH_WEBHOOK_URL'] = settings.webhook_url
            print("🔗 Found webhook URL in the configuration, notifications will be sent to the webhook")
            
            # Apply configuration using init_cluster.sh
            init_script = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'utils', 'init_cluster.sh')
            run_script(init_script)
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