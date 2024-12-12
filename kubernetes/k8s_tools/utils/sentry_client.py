import os
import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration

DEFAULT_DSN = "https://a376986fac23d5fee76f277fafdfeeb9@o1306664.ingest.us.sentry.io/4507939806248960"

def initialize_sentry():
    """Initialize Sentry with configuration"""
    dsn = os.getenv('KUBIYA_SENTRY_DSN', DEFAULT_DSN)
    
    # Enable logging integration
    sentry_logging = LoggingIntegration(
        level=os.getenv('SENTRY_LOG_LEVEL', 'INFO'),
        event_level=os.getenv('SENTRY_EVENT_LEVEL', 'ERROR')
    )
    
    sentry_sdk.init(
        dsn=dsn,
        traces_sample_rate=float(os.getenv('SENTRY_TRACE_SAMPLE_RATE', '1.0')),
        profiles_sample_rate=float(os.getenv('SENTRY_PROFILE_SAMPLE_RATE', '1.0')),
        environment=os.getenv('KUBIYA_ENV', 'production'),
        integrations=[sentry_logging],
        enable_tracing=True
    ) 