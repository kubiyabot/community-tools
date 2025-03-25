import os

def configure_localstack():
    """Configure environment for LocalStack if needed."""
    # Set default LocalStack values if not already set
    os.environ.setdefault('AWS_ACCESS_KEY_ID', 'test')
    os.environ.setdefault('AWS_SECRET_ACCESS_KEY', 'test')
    os.environ.setdefault('AWS_DEFAULT_REGION', 'us-east-1')
    os.environ.setdefault('AWS_ENDPOINT_URL', 'http://localhost:4566') 