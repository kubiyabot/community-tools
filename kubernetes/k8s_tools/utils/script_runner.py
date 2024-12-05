import subprocess
import shlex
import os
import sys

def run_script(script_content: str, env_vars: dict = None) -> str:
    """Run a script and stream output in real-time."""
    # Create a temporary script file
    script_path = '/tmp/kubiya_k8s_script.sh'
    with open(script_path, 'w') as f:
        f.write(script_content)
    os.chmod(script_path, 0o700)  # Make the script executable

    # Prepare the environment
    script_env = os.environ.copy()
    if env_vars:
        script_env.update(env_vars)

    try:
        # Run the script and stream output
        process = subprocess.Popen(
            ['/bin/bash', script_path],
            env=script_env,
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
                print(line.rstrip(), flush=True)  # Print to console
                output.append(line)  # Store for return value

        # Wait for process to complete and check return code
        return_code = process.wait()
        if return_code != 0:
            raise subprocess.CalledProcessError(return_code, script_path)

        return ''.join(output)

    finally:
        # Clean up the temporary script file
        if os.path.exists(script_path):
            os.remove(script_path)