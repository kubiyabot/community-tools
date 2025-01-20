try:
    from .tools import generate_iam_access_tools
    generate_iam_access_tools()
except ImportError:
    print("⚠️  Import Warning:")
    print("   This is expected during discovery phase and can be safely ignored.")
    print("   The required modules will be available during actual execution.")
    pass
