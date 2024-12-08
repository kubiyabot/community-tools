import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional
from jenkins_ops.config import DEFAULT_JENKINS_CONFIG

logger = logging.getLogger(__name__)

def validate_config(config: Dict[str, Any]) -> bool:
    """Basic configuration validation without jsonschema dependency."""
    try:
        # Validate required fields
        if not isinstance(config, dict):
            raise ValueError("Configuration must be a JSON object")

        # Validate jenkins_url
        if 'jenkins_url' not in config:
            raise ValueError("Missing required field 'jenkins_url'")
        if not isinstance(config['jenkins_url'], str):
            raise ValueError("'jenkins_url' must be a string")

        # Validate auth
        if 'auth' not in config:
            raise ValueError("Missing required field 'auth'")
        if not isinstance(config['auth'], dict):
            raise ValueError("'auth' must be an object")
        if 'username' not in config['auth']:
            raise ValueError("Missing required field 'auth.username'")
        if 'password_env' not in config['auth']:
            raise ValueError("Missing required field 'auth.password_env'")

        # Validate jobs configuration if present
        if 'jobs' in config:
            jobs = config['jobs']
            if not isinstance(jobs, dict):
                raise ValueError("'jobs' must be an object")
            
            if 'sync_all' in jobs and not isinstance(jobs['sync_all'], bool):
                raise ValueError("'jobs.sync_all' must be a boolean")
            
            if 'include' in jobs and not isinstance(jobs['include'], list):
                raise ValueError("'jobs.include' must be an array")
            
            if 'exclude' in jobs and not isinstance(jobs['exclude'], list):
                raise ValueError("'jobs.exclude' must be an array")

        # Validate defaults if present
        if 'defaults' in config:
            defaults = config['defaults']
            if not isinstance(defaults, dict):
                raise ValueError("'defaults' must be an object")
            
            if 'stream_logs' in defaults and not isinstance(defaults['stream_logs'], bool):
                raise ValueError("'defaults.stream_logs' must be a boolean")
            
            if 'poll_interval' in defaults and not isinstance(defaults['poll_interval'], int):
                raise ValueError("'defaults.poll_interval' must be an integer")
            
            if 'long_running_threshold' in defaults and not isinstance(defaults['long_running_threshold'], int):
                raise ValueError("'defaults.long_running_threshold' must be an integer")

        return True

    except Exception as e:
        logger.error(f"Configuration validation failed: {str(e)}")
        raise ValueError(f"Invalid configuration: {str(e)}")

def get_jenkins_config() -> Optional[Dict[str, Any]]:
    """Load and validate Jenkins configuration."""
    try:
        config_path = Path(__file__).parent / 'configs' / 'jenkins_config.json'
        
        # If config file exists, load it
        if config_path.exists():
            with open(config_path) as f:
                config = json.load(f)
        else:
            # Use default config
            logger.info("No configuration file found, using default in-cluster settings")
            config = DEFAULT_JENKINS_CONFIG.copy()

        # Validate configuration
        validate_config(config)

        # Set default values
        if 'defaults' not in config:
            config['defaults'] = {}
        config['defaults'].setdefault('stream_logs', True)
        config['defaults'].setdefault('poll_interval', 30)
        config['defaults'].setdefault('long_running_threshold', 300)

        return config

    except Exception as e:
        logger.error(f"Failed to load configuration: {str(e)}")
        return None 