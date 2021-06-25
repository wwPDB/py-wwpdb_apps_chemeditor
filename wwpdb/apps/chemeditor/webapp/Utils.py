from logging import getLogger, StreamHandler, Formatter, DEBUG, INFO

def setupLog(verbose, log_file):
    """Setup a Logger instance to use the same file as provided
    by the 'log' parameters

    Args:
        log_file (IOStream): a file-like object

    Returns:
        Logger: instance of Logger class
    """
    logger = getLogger(__name__)
    handler = StreamHandler(log_file)

    formatter = Formatter('+%(module)s.%(funcName)s() ++ %(message)s\n')
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    
    if verbose:
        logger.setLevel(DEBUG)
    else:
        logger.setLevel(INFO)

    return logger