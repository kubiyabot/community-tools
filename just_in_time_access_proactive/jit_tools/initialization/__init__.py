from ..utils.script_runner import run_script, ScriptExecutionError
import json
import os
import sys
import base64
from typing import Dict, Any, Optional
from kubiya_sdk.tools.registry import tool_registry


def get_opa_policy_template(config: Dict[str, Any]) -> str:
    policy_template = '''package kubiya.tool_manager

# Default deny all access
default allow = false

# Tool Categories
tool_categories := {
    "admin": {
        "list_active_access_requests",
        "view_user_requests",
        "approve_tool_access_request",
        "describe_access_request"
    },
    "revoke": {${revoke_tools}},
    "restricted": {${restricted_tools}}
}

# Helper functions
is_admin(user) {
    user.groups[_].name == "${approves_group_name}"
}

is_tool_in_category(tool_name, category) {
    tool_categories[category][tool_name]
}

# Rules
# Allow administrators to run admin tools
allow {
    is_admin(input.user)
    is_tool_in_category(input.tool.name, "admin")
}

# Allow administrators to run revoke tools
allow {
    is_admin(input.user)
    is_tool_in_category(input.tool.name, "revoke")
}

# Allow everyone to run non-admin, non-restricted tools
allow {
    # Check that the tool is not in any restricted category
    not is_tool_in_category(input.tool.name, "admin")
    not is_tool_in_category(input.tool.name, "restricted")
    not is_tool_in_category(input.tool.name, "revoke")
}

# Metadata for policy documentation
metadata := {
    "description": "Access control policy for Kubiya tool manager",
    "roles": {
        "admin": "Can access admin tools and revocation tools",
        "user": "Can access general tools except admin and restricted ones"
    },
    "categories": {
        "admin": "Administrative tools for managing access",
        "revoke": "Tools for revoking access",
        "restricted": "Tools with restricted access"
    }
}'''

    if config:
        revoke_tools: str = ""
        restricted_tools: str = ""
        revoke_tools_names: [] = []
        restricted_tools_names: [str] = []
        cfg = json.loads(config.get('aws_jit_config'))
        s3_config = cfg.get('s3_configs', {})
        session_config = cfg.get('access_configs', {})
        approves_group_name = config.get('approves_group_name')

        for key in s3_config:
            name = s3_config[key]['name'].lower().replace(' ', '_')
            if name:
                revoke_tools_names.append(f"s3_revoke_{name}")
                restricted_tools_names.append(f"s3_grant_{name}")

        for key in session_config:
            name = session_config[key]['name'].lower().replace(' ', '_')
            if name:
                revoke_tools_names.append(f"jit_session_revoke_{name}")
                restricted_tools_names.append(f"jit_session_grant_{name}")

        for i in range(len(revoke_tools_names)):
            if i == 0:
                revoke_tools += f"\n\t\t\"{revoke_tools_names[i]}\""
            elif i == len(revoke_tools_names) - 1:
                revoke_tools += f",\n\t\t\"{revoke_tools_names[i]}\"\n\t"
            else:
                revoke_tools += f",\n\t\t\"{revoke_tools_names[i]}\""

        for i in range(len(restricted_tools_names)):
            if i == 0:
                restricted_tools += f"\n\t\t\"{restricted_tools_names[i]}\""
            elif i == len(restricted_tools_names) - 1:
                restricted_tools += f",\n\t\t\"{restricted_tools_names[i]}\"\n\t"
            else:
                restricted_tools += f",\n\t\t\"{restricted_tools_names[i]}\""

        policy = policy_template.replace("${revoke_tools}", revoke_tools)
        policy = policy.replace("${restricted_tools}", restricted_tools)
        return policy.replace("${approves_group_name}", approves_group_name)
    else:
        raise ConfigurationError("No configuration provided is required.")


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
            raise ConfigurationError("No configuration provided is required.")

        # Try to load the config as a JSON object if it's a string
        if isinstance(config, str):
            try:
                config = json.loads(config)
            except json.JSONDecodeError:
                print("⚠️ Invalid JSON configuration format")
                raise ConfigurationError("Invalid configuration format")

        print(f"📝 Processing configuration in EnforcerConfigBuilder: {json.dumps(config, indent=2)}")

        settings.org = os.getenv("KUBIYA_USER_ORG")
        settings.runner = config.get('opa_runner_name')
        
        # Policy generation logic - either from AWS JIT config or use provided OPA policy
        if config.get('aws_jit_config'):
            print("📝 Found AWS JIT config, generating policy from template")
            settings.policy = get_opa_policy_template(config)
        elif config.get('opa_policy'):
            print("📝 Using provided OPA policy")
            settings.policy = config.get('opa_policy')
        else:
            raise ConfigurationError("Either aws_jit_config or opa_policy must be provided")

        print(f"📝 Final policy set in settings: {settings.policy}")

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

        # Get organization name from environment or config
        org_name = os.getenv("KUBIYA_USER_ORG") or config.get('org_name') or "default_org"
        runner_name = config.get('opa_runner_name') or "default_runner"
        policy = settings.policy or ""

        # Set environment variables with defaults
        os.environ['BS64_ORG_NAME'] = base64.b64encode(org_name.encode()).decode()
        os.environ['BS64_RUNNER_NAME'] = base64.b64encode(runner_name.encode()).decode()
        os.environ['BS64_OPA_DEFAULT_POLICY'] = base64.b64encode(policy.encode()).decode()

        # DataDog settings (optional)
        if settings.dd_api_key:
            os.environ['BS64_DATA_DOG_API_KEY'] = base64.b64encode(settings.dd_api_key.encode()).decode()
        if settings.dd_site:
            os.environ['BS64_DATA_DOG_SITE'] = base64.b64encode(settings.dd_site.encode()).decode()

        # Okta settings (optional)
        os.environ['IDP_PROVIDER'] = settings.idp_provider
        if settings.idp_provider == 'okta' and settings.okta_settings:
            os.environ['BS64_OKTA_BASE_URL'] = base64.b64encode(
                settings.okta_settings['okta_base_url'].encode()).decode()
            os.environ['BS64_OKTA_TOKEN_ENDPOINT'] = base64.b64encode(
                settings.okta_settings['okta_token_endpoint'].encode()).decode()
            os.environ['BS64_OKTA_CLIENT_ID'] = base64.b64encode(
                settings.okta_settings['okta_client_id'].encode()).decode()
            os.environ['BS64_PRIVATE_KEY'] = base64.b64encode(
                settings.okta_settings['okta_private_key'].encode()).decode()

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
