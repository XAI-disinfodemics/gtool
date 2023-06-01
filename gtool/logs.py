import logging
from argparse import ArgumentTypeError


def setup_logging(name):
    #logging.setLoggerClass(Logger) # Personalized Logger class
    return logging.getLogger(name)


def valid_loglevel(loglevel):
    if loglevel not in logging._nameToLevel.keys():
         raise ArgumentTypeError(
            "Not a valid level for loggings: {0!r}".format(loglevel)
        )
    return loglevel


def configure_logging(loglevel):
    rootLogger = logging.getLogger()

    # Set level
    if loglevel:
        level = logging.getLevelName(loglevel)
        rootLogger.setLevel(level)

    # Create formatter
    formatter = logging.Formatter('{asctime}.{msecs:03.0f}|{levelname}|{name}|{message}', datefmt = '%Y-%m-%d %H:%M:%S', style = '{')

    # Add stream handler
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    rootLogger.addHandler(handler)