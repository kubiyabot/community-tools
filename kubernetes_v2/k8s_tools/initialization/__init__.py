import os
import sys
import json
import logging
import sentry_sdk
from kubiya_workflow_sdk.tools.registry import tool_registry
from ..utils.script_runner import run_script, ScriptExecutionError
from ..utils.kubewatch_config import KubeWatchConfig
from ..utils.sentry_client import initialize_sentry

# Configure logging
logger = logging.getLogger(__name__)

def initialize():
    """Initialize Kubernetes tools and KubeWatch configuration."""
    try:
        logger.info("=== Starting KubeWatch Initialization ===")
        
        # Ensure Sentry is initialized
        initialize_sentry()
        
        # Get dynamic configuration
        config = tool_registry.dynamic_config
        sentry_sdk.add_breadcrumb(
            category='configuration',
            message='Received dynamic configuration',
            data={'config': config},
            level='info'
        )
        logger.info(f"📝 Received dynamic configuration: {config}")
        
        if not config:
            sentry_sdk.capture_message("No dynamic configuration provided", level='warning')
            print("⚠️  No dynamic configuration provided")
            return
        
        # Parse configuration using KubeWatchConfig
        settings = KubeWatchConfig.parse_config(config)
        sentry_sdk.add_breadcrumb(
            category='configuration',
            message='Parsed configuration settings',
            data={'settings': settings.__dict__},
            level='info'
        )
        print(f"✅ Parsed configuration settings: {settings.__dict__}")
        
        # Handle webhook URL first
        if not settings.webhook_url:
            sentry_sdk.capture_message(
                "No webhook URL provided - notifications will not be sent",
                level='warning'
            )
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
                    "batchSize": settings.numeric_settings.get('batch_size', 1),
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

        sentry_sdk.add_breadcrumb(
            category='configuration',
            message='Generated KubeWatch inner configuration',
            data={'inner_config': kubewatch_inner_config},
            level='info'
        )

        # Add namespaces to filter if specified
        if settings.namespaces and settings.namespaces != ['*']:
            kubewatch_inner_config["filter"]["namespaces"] = settings.namespaces
            sentry_sdk.add_breadcrumb(
                category='configuration',
                message='Watching specific namespaces',
                data={'namespaces': settings.namespaces},
                level='info'
            )
            print(f"🔍 Watching specific namespaces: {', '.join(settings.namespaces)}")
        else:
            sentry_sdk.add_breadcrumb(
                category='configuration',
                message='Watching all namespaces',
                level='info'
            )
            print("🔍 Watching all namespaces")

        # Write configurations
        try:
            inner_json_path = "/tmp/kubewatch_inner.json"
            with open(inner_json_path, 'w') as f:
                json.dump(kubewatch_inner_config, f, indent=2)
            
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
                    ".kubewatch.yaml": inner_json_path
                }
            }
            
            json_path = "/tmp/kubewatch.json"
            with open(json_path, 'w') as f:
                json.dump(kubewatch_config, f, indent=2)
            
            sentry_sdk.add_breadcrumb(
                category='configuration',
                message='Wrote configuration files',
                data={
                    'inner_path': inner_json_path,
                    'config_path': json_path
                },
                level='info'
            )
            
        except Exception as e:
            sentry_sdk.capture_exception(e)
            raise
        
        # Set environment variables and run initialization script
        try:
            os.environ['KUBIYA_KUBEWATCH_WEBHOOK_URL'] = settings.webhook_url
            os.environ['KUBEWATCH_CONFIG_PATH'] = json_path
            os.environ['KUBEWATCH_INNER_CONFIG_PATH'] = inner_json_path
            
            init_script = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'utils', 'init_cluster.sh')
            output = run_script(init_script)
            
            sentry_sdk.add_breadcrumb(
                category='initialization',
                message='Initialization script completed',
                data={'output': output},
                level='info'
            )
            
            sentry_sdk.capture_message(
                "KubeWatch initialization completed successfully",
                level='info'
            )
            
        except ScriptExecutionError as e:
            sentry_sdk.capture_exception(e)
            sentry_sdk.add_breadcrumb(
                category='initialization',
                message='Initialization script failed',
                data={
                    'error': e.message,
                    'output': e.output,
                    'error_output': e.error_output
                },
                level='error'
            )
            raise
        
        print("=== KubeWatch Initialization Completed ===\n")
        
    except Exception as e:
        logger.error(f"❌ Initialization failed: {str(e)}")
        sentry_sdk.capture_exception(e)
        raise

# Initialize Sentry when module is imported
initialize_sentry()

__all__ = ['initialize'] 