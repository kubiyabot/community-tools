import subprocess
import os
import sys
from kubiya_sdk.tools.registry import tool_registry

def run_script(script_path: str) -> str:
    """Run a script with proper environment variables."""
    try:
        # Get dynamic configuration
        config = tool_registry.dynamic_config or {}
        
        # Prepare environment variables
        env = os.environ.copy()
        
        # Map configuration to environment variables
        env_mapping = {
            'webhook_url': 'KUBIYA_KUBEWATCH_WEBHOOK_URL',
            'dedup_window': 'DEDUP_WINDOW',
            'batch_size': 'BATCH_SIZE',
            'max_wait_time': 'MAX_WAIT_TIME',
            'min_wait_time': 'MIN_WAIT_TIME',
            'max_log_lines': 'MAX_LOG_LINES',
            'max_events': 'MAX_EVENTS',
            'min_severity': 'MIN_SEVERITY',
            'watch_pod': 'WATCH_POD',
            'watch_node': 'WATCH_NODE',
            'watch_deployment': 'WATCH_DEPLOYMENT',
            'watch_service': 'WATCH_SERVICE',
            'watch_ingress': 'WATCH_INGRESS',
            'watch_event': 'WATCH_EVENT',
            'include_logs': 'INCLUDE_LOGS',
            'include_events': 'INCLUDE_EVENTS',
            'include_metrics': 'INCLUDE_METRICS'
        }
        
        # Set environment variables from config
        for config_key, env_key in env_mapping.items():
            if config_key in config:
                env[env_key] = str(config[config_key]).lower()
        
        # Run the script
        process = subprocess.Popen(
            ['bash', script_path],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )

        # Stream output in real-time
        output = []
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                print(line.rstrip(), flush=True)
                output.append(line)

        return_code = process.wait()
        if return_code != 0:
            raise subprocess.CalledProcessError(return_code, script_path)

        return ''.join(output)

    except Exception as e:
        print(f"❌ Script execution failed: {str(e)}", file=sys.stderr)
        raise