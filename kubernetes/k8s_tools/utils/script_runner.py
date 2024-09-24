import subprocess
import shlex
import os

def run_script(script_content: str, env_vars: dict = None) -> str:
    # Create a temporary script file
    script_path = '/tmp/kubiya_k8s_script.sh'
    with open(script_path, 'w') as f:
        f.write(script_content)
    os.chmod(script_path, 0o700)  # Make the script executable

    # Prepare the environment
    script_env = os.environ.copy()
    if env_vars:
        script_env.update(env_vars)

    # Run the script
    try:
        result = subprocess.run(
            ['/bin/bash', script_path],
            env=script_env,
            check=True,
            capture_output=True,
            text=True
        )
        return result.stdout
    finally:
        # Clean up the temporary script file
        os.remove(script_path)