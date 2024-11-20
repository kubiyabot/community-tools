import logging


def setup_logging(level=logging.INFO):
    """
    Set up logging for the SDK.
    :param level: Logging level (e.g., logging.DEBUG, logging.INFO).
    """
    logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=level)


def get_logger(name: str):
    """
    Get a logger with the specified name.
    :param name: The name of the logger.
    :return: Configured logger instance.
    """
    return logging.getLogger(name)
