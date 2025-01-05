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

        if not config:
            raise ConfigurationError(
                "No configuration provided. enfrocer dynamic config is required."
            )

        settings = type("EnforcerSettings", (), {})()
        
        settings.idp_provider = "kubiya"  # Default IDP provider
        settings.runner = config.get("runner")
        settings.org = os.getenv("KUBIYA_USER_ORG")
        settings.policy = config.get("opa_default_policy")
        
        
        if not settings.runner:
            raise ConfigurationError(f"Missing required field: runner")

        if not settings.policy:
            raise ConfigurationError(f"Missing required field: opa_default_policy")

        # Try to load the config as a JSON object if it's a string
        if isinstance(config, str):
            try:
                config = json.loads(config)
            except json.JSONDecodeError:
                print("⚠️ Invalid JSON configuration format")
                raise ConfigurationError("Invalid configuration format")

        print(f"📝 Processing configuration: {config}")

        # Check for Okta configuration
        okta_fields = [
            "okta_base_url",
            "okta_token_endpoint",
            "okta_client_id",
            "okta_private_key",
        ]
        okta_values = {field: config.get(field) for field in okta_fields}

        # If all Okta fields are present, use Okta as IDP
        if all(okta_values.values()):
            settings.idp_provider = "okta"
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

        settings.dd_site = config.get("dd_site")
        if settings.dd_site:
            print("✅ DataDog site detected")

        settings.dd_api_key = config.get("dd_api_key")
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
        os.environ["BS64_ORG_NAME"] = base64.b64encode(settings.org).decode()
        os.environ["BS64_RUNNER_NAME"] = base64.b64encode(settings.runner).decode()
        os.environ["BS64_OPA_DEFAULT_POLICY"] = base64.b64encode(
            settings.opa_default_policy
        ).decode()

        # DataBricks API Key (optional)
        if settings.dd_api_key:
            os.environ["BS64_DATA_DOG_API_KEY"] = base64.b64encode(
                settings.dd_api_key.encode()
            ).decode()

        # DataBricks API Key (optional)
        if settings.dd_site:
            os.environ["BS64_DATA_DOG_SITE"] = base64.b64encode(
                settings.dd_site.encode()
            ).decode()

        # Okta settings (optional)
        os.environ["IDP_PROVIDER"] = settings.idp_provider
        if settings.idp_provider == "okta":
            os.environ["BS64_OKTA_BASE_URL"] = base64.b64encode(
                settings.okta_settings["okta_base_url"].encode()
            ).decode()
            os.environ["BS64_OKTA_TOKEN_ENDPOINT"] = base64.b64encode(
                settings.okta_settings["okta_token_endpoint"].encode()
            ).decode()
            os.environ["BS64_OKTA_CLIENT_ID"] = base64.b64encode(
                settings.okta_settings["okta_client_id"].encode()
            ).decode()
            os.environ["BS64_PRIVATE_KEY"] = base64.b64encode(
                settings.okta_settings["okta_private_key"].encode()
            ).decode()

        # Apply configuration using init script
        init_script = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "utils", "init_enforcer.sh"
        )
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
