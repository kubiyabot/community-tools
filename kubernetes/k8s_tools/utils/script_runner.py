import subprocess
import os
import sys
from typing import Optional, Dict
from kubiya_sdk.tools.registry import tool_registry

class ScriptExecutionError(Exception):
    """Custom exception for script execution failures."""
    def __init__(self, message: str, script_path: str, exit_code: int, output: str):
        self.message = message
        self.script_path = script_path
        self.exit_code = exit_code
        self.output = output
        super().__init__(self.message)

def run_script(script_path: str, env_vars: Optional[Dict[str, str]] = None) -> str:
    """
    Run a script with proper environment variables and enhanced error handling.
    
    Args:
        script_path: Path to the script to execute
        env_vars: Additional environment variables to set
    
    Returns:
        str: Script output
    
    Raises:
        ScriptExecutionError: If script execution fails
        FileNotFoundError: If script file doesn't exist
        PermissionError: If script isn't executable
    """
    try:
        # Convert to absolute path
        script_path = os.path.abspath(script_path)
        
        # Verify script exists and is executable
        if not os.path.exists(script_path):
            raise FileNotFoundError(f"Script not found: {script_path}")
        
        if not os.access(script_path, os.X_OK):
            try:
                os.chmod(script_path, 0o755)  # Make executable if not already
            except Exception as e:
                raise PermissionError(f"Cannot make script executable: {str(e)}")
        
        print(f"🔄 Executing script: {os.path.basename(script_path)}")
        print(f"📂 Script path: {script_path}")
        
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
        
        # Add any additional environment variables
        if env_vars:
            env.update(env_vars)
        
        print(f"🔄 Executing script: {os.path.basename(script_path)}")
        
        # Run the script
        process = subprocess.Popen(
            ['bash', script_path],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            bufsize=1
        )

        # Collect output and stream in real-time
        output_lines = []
        error_lines = []
        
        while True:
            # Read from stdout
            stdout_line = process.stdout.readline()
            if stdout_line:
                print(stdout_line.rstrip(), flush=True)
                output_lines.append(stdout_line)
            
            # Read from stderr
            stderr_line = process.stderr.readline()
            if stderr_line:
                print(f"❌ {stderr_line.rstrip()}", file=sys.stderr, flush=True)
                error_lines.append(stderr_line)
            
            # Check if process has finished
            if process.poll() is not None:
                # Read any remaining output
                for line in process.stdout.readlines():
                    print(line.rstrip(), flush=True)
                    output_lines.append(line)
                for line in process.stderr.readlines():
                    print(f"❌ {line.rstrip()}", file=sys.stderr, flush=True)
                    error_lines.append(line)
                break

        return_code = process.wait()
        
        # Combine all output
        all_output = ''.join(output_lines)
        error_output = ''.join(error_lines)
        
        if return_code != 0:
            error_msg = (
                f"Script execution failed (exit code: {return_code})\n"
                f"Script: {script_path}\n"
                f"Error output:\n{error_output}\n"
                f"Standard output:\n{all_output}"
            )
            raise ScriptExecutionError(
                message=error_msg,
                script_path=script_path,
                exit_code=return_code,
                output=all_output + error_output
            )

        return all_output

    except ScriptExecutionError:
        raise
    except Exception as e:
        error_msg = f"Failed to execute script {script_path}: {str(e)}"
        print(f"❌ {error_msg}", file=sys.stderr)
        raise ScriptExecutionError(
            message=error_msg,
            script_path=script_path,
            exit_code=-1,
            output=str(e)
        ) from e