import subprocess
import logging
import os
from typing import Optional, Dict

logger = logging.getLogger(__name__)

def run_command(
    command: str,
    env_vars: Optional[Dict[str, str]] = None,
    check: bool = True
) -> str:
    """
    Run a shell command with proper error handling.
    
    Args:
        command: The command to run
        env_vars: Optional environment variables
        check: Whether to raise an exception on non-zero exit code
    
    Returns:
        Command output as string
    
    Raises:
        subprocess.CalledProcessError: If command fails and check=True
    """
    try:
        env = os.environ.copy()
        if env_vars:
            env.update(env_vars)
            
        result = subprocess.run(
            command,
            shell=True,
            check=check,
            text=True,
            capture_output=True,
            env=env
        )
        
        if result.stderr:
            logger.warning(f"Command stderr: {result.stderr}")
            
        return result.stdout.strip()
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed with exit code {e.returncode}")
        logger.error(f"Error output: {e.stderr}")
        raise 