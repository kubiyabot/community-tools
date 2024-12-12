import subprocess
import os
import sys
from typing import Optional, Dict
from kubiya_sdk.tools.registry import tool_registry

class ScriptExecutionError(Exception):
    """Custom exception for script execution failures."""
    def __init__(self, message: str, script_path: str, exit_code: int, output: str, error_output: str):
        self.message = message
        self.script_path = script_path
        self.exit_code = exit_code
        self.output = output
        self.error_output = error_output
        
        # Format detailed error message
        self.detailed_message = (
            f"{message}\n\n"
            f"Script: {script_path}\n"
            f"Exit Code: {exit_code}\n"
            f"Error Output:\n{error_output}\n"
            f"Standard Output:\n{output}"
        )
        super().__init__(self.detailed_message)

def run_script(script_path: str, env_vars: Optional[Dict[str, str]] = None) -> str:
    """
    Run a script with proper environment variables and enhanced error handling.
    
    Args:
        script_path: Path to the script to execute
        env_vars: Additional environment variables to set
    
    Returns:
        str: Script output
    
    Raises:
        ScriptExecutionError: If script execution fails with detailed error info
    """
    try:
        # Convert to absolute path
        script_path = os.path.abspath(script_path)
        
        # Verify script exists
        if not os.path.exists(script_path):
            raise ScriptExecutionError(
                message=f"Script not found: {script_path}",
                script_path=script_path,
                exit_code=1,
                output="",
                error_output="File does not exist"
            )
        
        # Make script executable
        try:
            os.chmod(script_path, 0o755)
        except Exception as e:
            raise ScriptExecutionError(
                message="Failed to make script executable",
                script_path=script_path,
                exit_code=1,
                output="",
                error_output=str(e)
            )
        
        # Prepare environment variables
        env = os.environ.copy()
        if env_vars:
            env.update(env_vars)
        
        # Run the script
        process = subprocess.Popen(
            ['bash', script_path],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            bufsize=1
        )

        # Collect output
        stdout, stderr = process.communicate()
        return_code = process.returncode
        
        if return_code != 0:
            # Map common error codes to meaningful messages
            error_messages = {
                127: "Command not found - Missing required dependencies",
                1: "General error occurred",
                126: "Command invoked cannot execute - Permission problem or command is not executable",
                2: "Command syntax error or invalid argument",
            }
            
            error_msg = error_messages.get(return_code, f"Command failed with exit code {return_code}")
            
            raise ScriptExecutionError(
                message=error_msg,
                script_path=script_path,
                exit_code=return_code,
                output=stdout,
                error_output=stderr
            )

        return stdout

    except ScriptExecutionError:
        raise
    except Exception as e:
        raise ScriptExecutionError(
            message=f"Unexpected error during script execution",
            script_path=script_path,
            exit_code=-1,
            output="",
            error_output=str(e)
        ) from e

# Explicitly export the classes and functions
__all__ = ['ScriptExecutionError', 'run_script']