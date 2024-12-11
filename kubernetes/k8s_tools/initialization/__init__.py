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
        
        # Generate inner KubeWatch configuration first
        kubewatch_inner_config = {
            "version": "1",
            "logging": {
                "level": "debug",
                "format": "text",
                "fields": {
                    "component": "kubiya-kubernetes-watcher"
                }
            },
            "filter": {
                "watch_for": [
                    {
                        "kind": "Pod",
                        "reasons": [
                            "*CrashLoopBackOff*",
                            "*OOMKilled*",
                            "*ImagePullBackOff*",
                            "*RunContainerError*",
                            "*Failed*"
                        ],
                        "severity": "critical"
                    },
                    {
                        "kind": "Node",
                        "reasons": [
                            "*NotReady*",
                            "*DiskPressure*",
                            "*MemoryPressure*",
                            "*NetworkUnavailable*"
                        ],
                        "severity": "critical"
                    }
                ],
                "settings": {
                    "dedup_interval": settings.numeric_settings.get('dedup_window', '15m'),
                    "include_labels": True,
                    "namespace_isolation": settings.advanced_settings.get('namespace_isolation', False),
                    "group_by": ["owner", "app_label"]
                },
                "correlation": {
                    "ttl": "15m",
                    "max_events": 50,
                    "patterns": [
                        {
                            "resources": ["Deployment", "ReplicaSet", "Pod"],
                            "reasons": ["*Failed*", "CrashLoopBackOff"]
                        }
                    ]
                }
            },
            "handler": {
                "webhook": {
                    "url": settings.webhook_url,
                    "batchSize": settings.numeric_settings.get('batch_size', 5),
                    "min_wait": settings.numeric_settings.get('min_wait_time', '1m'),
                    "max_wait": settings.numeric_settings.get('max_wait_time', '2m'),
                    "filtering": {
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
                "event": settings.watch_settings.get('watch_event', True)
            },
            "enrichment": {
                "include_logs": settings.advanced_settings.get('include_logs', True),
                "include_events": settings.advanced_settings.get('include_events', True),
                "max_log_lines": settings.numeric_settings.get('max_log_lines', 50),
                "max_events": settings.numeric_settings.get('max_events', 10)
            }
        }

        # Write inner config as JSON to /tmp
        inner_json_path = "/tmp/kubewatch_inner.json"
        with open(inner_json_path, 'w') as f:
            json.dump(kubewatch_inner_config, f, indent=2)

        # Create outer ConfigMap structure
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
                ".kubewatch.yaml": inner_json_path  # This will be processed by yq in the shell script
            }
        }
        
        # Write outer config as JSON to /tmp
        json_path = "/tmp/kubewatch.json"
        print(f"📝 Writing KubeWatch configuration to: {json_path}")
        
        try:
            with open(json_path, 'w') as f:
                json.dump(kubewatch_config, f, indent=2)
            print(f"✅ Successfully wrote configuration to {json_path}")
        except Exception as e:
            print(f"❌ Failed to write configuration: {str(e)}")
            raise
        
        # Set environment variables for the script
        os.environ['KUBIYA_KUBEWATCH_WEBHOOK_URL'] = settings.webhook_url
        os.environ['KUBEWATCH_CONFIG_PATH'] = json_path
        os.environ['KUBEWATCH_INNER_CONFIG_PATH'] = inner_json_path
        print(f"🔗 Found webhook URL, will configure notifications")
        print(f"📁 Configuration paths:")
        print(f"  • Outer config: {json_path}")
        print(f"  • Inner config: {inner_json_path}")
        
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