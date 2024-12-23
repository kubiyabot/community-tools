from ..utils.script_runner import run_script, ScriptExecutionError
import json
import os
import sys
import base64
from typing import Dict, Any, Optional
from kubiya_sdk.tools.registry import tool_registry

class ConfigurationError(Exception):
    """Custom exception for configuration related errors"""
    pass

class EnforcerConfigBuilder:
    @staticmethod
    def parse_config(config: Optional[Dict[str, Any]] = None):
        """Parse configuration settings for Enforcer"""
        settings = type('EnforcerSettings', (), {})()
        settings.idp_provider = 'kubiya'  # Default IDP provider

        if not config:
            raise ConfigurationError("No configuration provided. opal_policy_url is required.")

        # Try to load the config as a JSON object if it's a string
        if isinstance(config, str):
            try:
                config = json.loads(config)
            except json.JSONDecodeError:
                print("⚠️ Invalid JSON configuration format")
                raise ConfigurationError("Invalid configuration format")

        print(f"📝 Processing configuration: {config}")

        # Required: Get policy repo url
        settings.opal_policy_url = config.get('opal_policy_url')
        if not settings.opal_policy_url:
            raise ConfigurationError(f"Missing required field: opal_policy_url")

        # Optional with default: policy branch
        settings.opal_policy_branch = config.get('opal_policy_branch', 'main')
        print(f"Using branch: {settings.opal_policy_branch} {'(default)' if 'opal_policy_branch' not in config else ''}")

        # Optional: Git deploy key
        settings.git_deploy_key = config.get('git_deploy_key')
        if settings.git_deploy_key:
            print("✅ Git deploy key configuration detected")

        # Check for Okta configuration
        okta_fields = ['okta_base_url', 'okta_token_endpoint', 
                      'okta_client_id', 'okta_private_key']
        okta_values = {
            field: config.get(field)
            for field in okta_fields
        }
        
        # If all Okta fields are present, use Okta as IDP
        if all(okta_values.values()):
            settings.idp_provider = 'okta'
            settings.okta_settings = okta_values
            print("✅ Okta configuration detected - using Okta as IDP provider")
        elif any(okta_values.values()):
            # If some Okta fields are present but not all
            missing = [f for f in okta_fields if not okta_values.get(f)]
            print(f"⚠️ Incomplete Okta configuration - missing: {missing}")
            print("⚠️ Falling back to kubiya IDP")
            settings.okta_settings = None
        else:
            print("✅ Using kubiya IDP")
            settings.okta_settings = None

        settings.dd_site = config.get('dd_site')  
        if settings.dd_site:
            print("✅ DataDog site detected")

        settings.dd_api_key = config.get('dd_api_key')  
        if settings.dd_api_key:
            print("✅ DataDog API Key detected")    

        return settings

def initialize():
    """Initialize Enforcer components and configuration."""
    try:
        print("\n=== Starting Enforcer Initialization ===")
        
        # Get configuration from tool registry
        dynamic_config = tool_registry.dynamic_config
        print(f"📝 Received dynamic configuration: {dynamic_config}")
        
        if dynamic_config:
            # If dynamic_config is already a dict with the required keys, use it directly
            if isinstance(dynamic_config, dict):
                config = dynamic_config
            else:
                # Try to parse the configuration
                try:
                    config = json.loads(dynamic_config)
                except json.JSONDecodeError:
                    raise ConfigurationError("Invalid configuration format")
        else:
            raise ConfigurationError("No configuration found in tool registry")
        
        print(f"📝 Using configuration: {config}")
        
        # Parse configuration using builder
        settings = EnforcerConfigBuilder.parse_config(config)
        print(f"✅ Using configuration settings: {settings.__dict__}")

        # Set environment variables for shell script
        # Required settings
        os.environ['OPAL_POLICY_REPO_URL_B64'] = base64.b64encode(settings.opal_policy_url.encode()).decode()
        os.environ['OPAL_POLICY_REPO_MAIN_BRANCH_B64'] = base64.b64encode(settings.opal_policy_branch.encode()).decode()

        # Git deploy key (optional)
        if settings.git_deploy_key:
            os.environ['GIT_DEPLOY_KEY_BS64'] = base64.b64encode(settings.git_deploy_key.encode()).decode()

        # DataBricks API Key (optional)
        if settings.dd_api_key:
            os.environ['DATA_DOG_API_KEY_BASE64'] = base64.b64encode(settings.dd_api_key.encode()).decode()

        # DataBricks API Key (optional)
        if settings.dd_site:
            os.environ['DATA_DOG_SITE_BASE64'] = base64.b64encode(settings.dd_site.encode()).decode()    

        # Okta settings (optional)
        os.environ['IDP_PROVIDER'] = settings.idp_provider
        if settings.idp_provider == 'okta':
            os.environ['OKTA_BASE_URL_B64'] = base64.b64encode(settings.okta_settings['okta_base_url'].encode()).decode()
            os.environ['OKTA_TOKEN_ENDPOINT_B64'] = base64.b64encode(settings.okta_settings['okta_token_endpoint'].encode()).decode()
            os.environ['OKTA_CLIENT_ID_B64'] = base64.b64encode(settings.okta_settings['okta_client_id'].encode()).decode()
            os.environ['PRIVATE_KEY_B64'] = base64.b64encode(settings.okta_settings['okta_private_key'].encode()).decode()
        
        # Apply configuration using init script
        init_script = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'utils', 'init_enforcer.sh')
        print(f"🔄 Running initialization script: {init_script}")
        
        try:
            output = run_script(init_script)
            print(f"✅ Initialization script completed successfully")
            print(f"Script output:\n{output}")
        except ScriptExecutionError as e:
            print(f"❌ Initialization script failed:")
            print(f"Error: {e.message}")
            print(f"Output: {e.output}")
            print(f"Error Output: {e.error_output}")
            raise
        
        print("=== Enforcer Initialization Completed ===\n")
        
    except Exception as e:
        print(f"❌ Initialization failed: {str(e)}", file=sys.stderr)
        raise