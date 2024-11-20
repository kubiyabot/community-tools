import logging


# Set up a basic logger configuration
def setup_logging(level=logging.INFO):
    logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=level)


# Create a logger for the SDK
logger = logging.getLogger("kubiya_sdk")
