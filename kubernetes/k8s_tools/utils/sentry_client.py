import os
import sys
import logging
import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DEFAULT_DSN = "https://a376986fac23d5fee76f277fafdfeeb9@o1306664.ingest.us.sentry.io/4507939806248960"

def initialize_sentry(force=False):
    """Initialize Sentry with configuration"""
    try:
        # Force re-initialization if requested
        if force and sentry_sdk.Hub.current.client is not None:
            logger.info("Forcing Sentry re-initialization")
            sentry_sdk.Hub.current.bind_client(None)

        if sentry_sdk.Hub.current.client is not None:
            logger.info("Sentry already initialized")
            # Send a test event even if already initialized
            sentry_sdk.capture_message("Sentry connection test (existing client)", level='info')
            return

        dsn = os.getenv('KUBIYA_SENTRY_DSN', DEFAULT_DSN)
        logger.info(f"Initializing Sentry with DSN: {dsn}")
        
        # Enable logging integration
        sentry_logging = LoggingIntegration(
            level=logging.INFO,  # Capture all INFO logs
            event_level=logging.ERROR  # Send errors as events
        )
        
        # Initialize with debug settings
        sentry_sdk.init(
            dsn=dsn,
            traces_sample_rate=1.0,  # Capture all traces
            profiles_sample_rate=1.0,  # Capture all profiles
            environment=os.getenv('KUBIYA_ENV', 'production'),
            integrations=[sentry_logging],
            debug=True,  # Enable debug mode
            enable_tracing=True,
            attach_stacktrace=True,
            before_send=before_send,  # Add context to events
        )
        
        # Send immediate test events
        logger.info("Sending test events to Sentry...")
        sentry_sdk.set_tag('test_initialization', 'true')
        
        # Test error
        try:
            raise ValueError("Test error for Sentry initialization")
        except Exception as e:
            sentry_sdk.capture_exception(e)
        
        # Test message
        sentry_sdk.capture_message(
            "Sentry initialization test message",
            level='info',
        )
        
        logger.info("Sentry initialized successfully - test events sent")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize Sentry: {str(e)}", exc_info=True)
        # Don't raise the exception - we want the application to continue even if Sentry fails
        return False

def before_send(event, hint):
    """Add additional context to events"""
    try:
        # Add Python version
        event['contexts']['runtime'] = {
            'name': 'Python',
            'version': sys.version
        }
        
        # Add environment info
        event['contexts']['environment'] = {
            'KUBIYA_ENV': os.getenv('KUBIYA_ENV', 'production'),
            'PYTHONPATH': os.getenv('PYTHONPATH', ''),
            'PWD': os.getcwd()
        }
        
    except Exception as e:
        logger.error(f"Error in before_send: {str(e)}")
    
    return event

# Initialize Sentry when module is imported - force initialization
if not initialize_sentry(force=True):
    logger.error("⚠️ Failed to initialize Sentry - continuing without error tracking")
else:
    logger.info("✅ Sentry initialized successfully") 