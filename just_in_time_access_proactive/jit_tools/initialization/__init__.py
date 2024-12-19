class EnforcerConfigBuilder:
    @staticmethod
    def parse_config(config):
        """Parse configuration settings for Enforcer"""
        settings = type('EnforcerSettings', (), {})()
        
        # Basic Postgres settings
        settings.postgres_settings = {
            'db': config.get('postgres_db', 'postgres'),
            'user': config.get('postgres_user', 'postgres'),
            'password': config.get('postgres_password', 'postgres')
        }

        # IDP Provider settings
        settings.idp_provider = config.get('idp_provider_name', 'kubiya')
        
        # Okta-specific settings if provider is Okta
        if settings.idp_provider == 'okta':
            settings.okta_settings = {
                'base_url': config.get('okta_base_url'),
                'token_endpoint': config.get('okta_token_endpoint'),
                'client_id': config.get('okta_client_id'),
                'private_key': config.get('okta_private_key')
            }
            
            # Validate required Okta settings
            missing_settings = [k for k, v in settings.okta_settings.items() if not v]
            if missing_settings:
                raise ValueError(f"Missing required Okta settings: {', '.join(missing_settings)}")
        
        return settings

def initialize():
    print("\n=== Starting Enforcer Initialization ===")
    print("\n=== Starting Enforcer Initialization ===")
    print("\n=== Starting Enforcer Initialization ===")
    print("\n=== Starting Enforcer Initialization ===")

    print("\n=== ============= ===")
    """Initialize Enforcer components and configuration."""
    try:
        print("\n=== Starting Enforcer Initialization ===")
        
        # Get dynamic configuration
        config = tool_registry.dynamic_config
        print(f"📝 Received dynamic configuration: {config}")
        
        if not config:
            print("⚠️  No dynamic configuration provided, using defaults")
            config = {}
        
        # Parse configuration using builder
        settings = EnforcerConfigBuilder.parse_config(config)
        print(f"✅ Parsed configuration settings: {settings.__dict__}")
        
        # Create Secret configuration
        secret_config = {
            "apiVersion": "v1",
            "kind": "Secret",
            "metadata": {
                "name": "opawatchdog-secrets",
                "namespace": "kubiya"
            },
            "type": "Opaque",
            "data": {
                "POSTGRES_DB": settings.postgres_settings['db'].encode('utf-8').hex(),
                "POSTGRES_USER": settings.postgres_settings['user'].encode('utf-8').hex(),
                "POSTGRES_PASSWORD": settings.postgres_settings['password'].encode('utf-8').hex()
            }
        }
        
        # Add Okta secrets if provider is Okta
        if settings.idp_provider == 'okta':
            secret_config["data"].update({
                "OKTA_BASE_URL": settings.okta_settings['base_url'].encode('utf-8').hex(),
                "OKTA_TOKEN_ENDPOINT": settings.okta_settings['token_endpoint'].encode('utf-8').hex(),
                "OKTA_CLIENT_ID": settings.okta_settings['client_id'].encode('utf-8').hex(),
                "OKTA_PRIVATE_KEY": settings.okta_settings['private_key'].encode('utf-8').hex()
            })
            print("✅ Added Okta configuration to secrets")
        
        # Write secret config
        secret_path = "/tmp/enforcer_secrets.json"
        with open(secret_path, 'w') as f:
            json.dump(secret_config, f, indent=2)
        
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