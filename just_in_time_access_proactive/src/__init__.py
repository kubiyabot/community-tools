def initialize():
    """Initialize JIT tools and Enforcer configuration."""
    try:
        print("Starting Enforcer set up...")
        from .initialization import initialize as init_cluster_setup
        init_cluster_setup()
        print("Enforcer tools initialization completed")
    except Exception as e:
        print(f"Failed to initialize Enforcer : {str(e)}")
        raise

# Run initialization when module is imported
print("Loading JIT tools module...")
initialize()

# Import tools after initialization
# from . import tools

# __all__ = ['tools']