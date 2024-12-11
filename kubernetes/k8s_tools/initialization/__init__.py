import os
import sys
import json
from kubiya_sdk.tools.registry import tool_registry
from ..utils.script_runner import run_script, ScriptExecutionError
from ..kubewatch.builder import KubeWatchConfigBuilder

def initialize():
    """Initialize Kubernetes tools and KubeWatch configuration."""
    try:
        print("\n=== Starting KubeWatch Initialization ===")
        
        # Get dynamic configuration
        config = tool_registry.dynamic_config
        print(f"📝 Received dynamic configuration: {config}")
        
        if not config:
            print("⚠️  No dynamic configuration provided")
            return
        
        # Parse configuration using builder
        settings = KubeWatchConfigBuilder.parse_config(config)
        print(f"✅ Parsed configuration settings: {settings.__dict__}")
        
        # Handle webhook URL first
        if not settings.webhook_url:
            print("⚠️  No webhook URL provided - notifications will not be sent")
            if 'KUBIYA_KUBEWATCH_WEBHOOK_URL' in os.environ:
                del os.environ['KUBIYA_KUBEWATCH_WEBHOOK_URL']
            return
        
        # Generate KubeWatch configuration with actual values
        print("Generating KubeWatch configuration...")
        kubewatch_yaml = {
            "version": "1",
            "filter": {
                "watch_for": [],  # Will be populated by init_cluster.sh
                "settings": {
                    "dedup_interval": settings.numeric_settings.get('dedup_window', '15m'),
                    "include_labels": True,
                    "namespace_isolation": settings.advanced_settings.get('namespace_isolation', False),
                    "group_by": ["owner", "app_label"],
                    "log_tail": settings.numeric_settings.get('max_log_lines', 50)
                }
            },
            "handler": {
                "webhook": {
                    "url": settings.webhook_url,
                    "batchSize": settings.numeric_settings.get('batch_size', 5),
                    "maxWaitTime": settings.numeric_settings.get('max_wait_time', '30s'),
                    "minWaitTime": settings.numeric_settings.get('min_wait_time', '5s'),
                    "groupEvents": settings.advanced_settings.get('group_events', True),
                    "groupBy": ["kind", "namespace", "reason", "owner"],
                    "filtering": {
                        "includeRoutineEvents": False,
                        "minSeverity": settings.advanced_settings.get('min_severity', 'Warning'),
                        "deduplication": {
                            "enabled": True,
                            "window": settings.numeric_settings.get('dedup_window', '15m')
                        }
                    }
                }
            },
            "resource": {
                "pod": settings.watch_settings.get('watch_pod', True),
                "node": settings.watch_settings.get('watch_node', True),
                "deployment": settings.watch_settings.get('watch_deployment', True),
                "service": settings.watch_settings.get('watch_service', False),
                "ingress": settings.watch_settings.get('watch_ingress', False),
                "event": settings.watch_settings.get('watch_event', True)
            },
            "enrichment": {
                "include_logs": settings.advanced_settings.get('include_logs', True),
                "include_events": settings.advanced_settings.get('include_events', True),
                "include_metrics": settings.advanced_settings.get('include_metrics', True),
                "max_log_lines": settings.numeric_settings.get('max_log_lines', 50),
                "max_events": settings.numeric_settings.get('max_events', 10)
            }
        }

        # Create the ConfigMap structure
        kubewatch_config = {
            "apiVersion": "v1",
            "kind": "ConfigMap",
            "metadata": {
                "name": "kubewatch-config",
                "namespace": "kubiya",
                "labels": {
                    "app.kubernetes.io/name": "kubewatch",
                    "app.kubernetes.io/part-of": "kubiya"
                }
            },
            "data": {
                ".kubewatch.yaml": kubewatch_yaml
            }
        }
        
        # Write configuration as JSON to /tmp
        json_path = "/tmp/kubewatch.json"
        print(f"📝 Writing KubeWatch configuration to: {json_path}")
        
        try:
            with open(json_path, 'w') as f:
                json.dump(kubewatch_config, f, indent=2)
            print(f"✅ Successfully wrote configuration to {json_path}")
        except Exception as e:
            print(f"❌ Failed to write configuration: {str(e)}")
            raise
        
        print(f"✅ Generated JSON configuration:")
        try:
            with open(json_path, 'r') as f:
                print(f.read())
        except Exception as e:
            print(f"❌ Failed to read back configuration: {str(e)}")
            raise
        
        # Set environment variables for the script
        os.environ['KUBIYA_KUBEWATCH_WEBHOOK_URL'] = settings.webhook_url
        os.environ['KUBEWATCH_CONFIG_PATH'] = json_path
        print(f"🔗 Found webhook URL, will configure notifications")
        print(f"📁 Configuration path: {json_path}")
        
        # Apply configuration using init_cluster.sh
        init_script = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'utils', 'init_cluster.sh')
        print(f"🔄 Running initialization script: {init_script}")
        
        try:
            output = run_script(init_script)
            print(f"✅ Initialization script completed successfully")
            print(f"Script output:\n{output}")
        except ScriptExecutionError as e:
            print(f"❌ Initialization script failed:")
            print(f"Error: {e.message}")
            print(f"Output: {e.output}")
            print(f"Error Output: {e.error_output}")
            raise
        
        print("=== KubeWatch Initialization Completed ===\n")
        
    except Exception as e:
        print(f"❌ Initialization failed: {str(e)}", file=sys.stderr)
        raise

__all__ = ['initialize'] 