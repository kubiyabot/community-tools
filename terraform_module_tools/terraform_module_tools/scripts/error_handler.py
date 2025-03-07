#!/usr/bin/env python3
import os
import sys
import logging
from functools import wraps
from typing import Optional, Callable

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class ScriptError(Exception):
    """Custom exception for script errors with exit code."""
    def __init__(self, message: str, exit_code: int = 1):
        self.message = message
        self.exit_code = exit_code
        super().__init__(self.message)

def validate_environment_vars(*required_vars: str) -> None:
    """Validate that required environment variables are set."""
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    if missing_vars:
        raise ScriptError(
            f"Missing required environment variables: {', '.join(missing_vars)}",
            exit_code=2
        )

def handle_script_error(func: Callable) -> Callable:
    """Decorator to handle script errors and logging."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ScriptError as e:
            logger.error(f"Script Error: {e.message}")
            sys.exit(e.exit_code)
        except Exception as e:
            logger.error(f"Unexpected Error: {str(e)}")
            sys.exit(1)
    return wrapper

# Export necessary components
__all__ = ['ScriptError', 'handle_script_error', 'validate_environment_vars', 'logger'] 