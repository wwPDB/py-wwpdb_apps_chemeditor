from logging import getLogger, StreamHandler, Formatter, DEBUG, INFO

HANDLER_NAME = 'stream_handler'


def setupLog(verbose, log_file):
    """Setup a Logger instance to use the same file as provided
    by the 'log' parameters

    Args:
        log_file (IOStream): a file-like object

    Returns:
        Logger: instance of Logger class
    """
    logger = getLogger(__name__)

    if logger.hasHandlers():
        for h in logger.handlers:
            # this field is not documented
            if h.get_name() == HANDLER_NAME:
                return logger

    handler = StreamHandler(log_file)
    handler.set_name(HANDLER_NAME)

    formatter = Formatter('+%(module)s.%(funcName)s() ++ %(message)s\n')
    handler.setFormatter(formatter)

    logger.addHandler(handler)

    if verbose:
        logger.setLevel(DEBUG)
    else:
        logger.setLevel(INFO)

    return logger
