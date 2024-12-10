import os
import sys
import yaml
from kubiya_sdk.tools.registry import tool_registry
from ..utils.script_runner import run_script
from .builder import KubeWatchConfigBuilder

def initialize():
    """Initialize the Kubernetes tools environment."""
    try:
        # Get and parse configuration
        config = tool_registry.dynamic_config
        settings = KubeWatchConfigBuilder.parse_config(config)
        
        # Generate configuration
        kubewatch_config = KubeWatchConfigBuilder.generate_config(settings)
        
        # Write configuration
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'kubewatch.yaml')
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        with open(config_path, 'w') as f:
            yaml.dump(kubewatch_config, f, default_flow_style=False)
        
        # Handle webhook URL
        if settings.webhook_url:
            os.environ['KUBIYA_KUBEWATCH_WEBHOOK_URL'] = settings.webhook_url
            print("🔗 Webhook URL configured")
            
            # Apply configuration
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
