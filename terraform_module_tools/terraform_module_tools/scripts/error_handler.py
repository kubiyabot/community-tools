#!/usr/bin/env python3
import sys
import traceback
import logging
from typing import Optional, Any, Callable
from functools import wraps

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ScriptError(Exception):
    """Custom exception for script errors with exit code."""
    def __init__(self, message: str, exit_code: int = 1):
        self.message = message
        self.exit_code = exit_code
        super().__init__(self.message)

def handle_script_error(func: Callable) -> Callable:
    """Decorator to handle script errors and ensure proper exit codes."""
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except ScriptError as e:
            logger.error(f"Script Error: {e.message}")
            sys.exit(e.exit_code)
        except Exception as e:
            logger.error(f"Unexpected Error: {str(e)}")
            logger.debug(f"Stack trace:\n{traceback.format_exc()}")
            sys.exit(1)
    return wrapper

def exit_with_error(message: str, exit_code: int = 1) -> None:
    """Exit the script with an error message and specific exit code."""
    logger.error(message)
    sys.exit(exit_code)

def validate_environment_vars(*required_vars: str) -> None:
    """Validate that required environment variables are set."""
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    if missing_vars:
        raise ScriptError(
            f"Missing required environment variables: {', '.join(missing_vars)}",
            exit_code=2
        ) 