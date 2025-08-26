import typing as t
import logging
import threading

_logger: t.Optional[logging.Logger] = None
_logger_lock = threading.RLock()

LOGGER_NAME = 'ts-deepscan'
DEFAULT_LOGGING_FORMAT = '[%(levelname)s] %(message)s'


def debug(msg, *args):
    if _logger:
        _logger.debug(msg, *args, stacklevel=2)


def info(msg, *args):
    if _logger:
        _logger.info(msg, *args, stacklevel=2)


def warning(msg, *args):
    if _logger:
        _logger.warning(msg, *args, stacklevel=2)


def error(msg, *args):
    if _logger:
        _logger.error(msg, *args, stacklevel=2)


def get_logger():
    global _logger

    _logger_lock.acquire()
    try:
        if not _logger:
            _logger = logging.getLogger(LOGGER_NAME)
            _logger.propagate = False

    finally:
        _logger_lock.release()

    return _logger


def log_to_console(level: t.Optional[int] = None):
    """
    Turn on logging and redirect it to tqdm's console output.
    """
    from tqdm.contrib.logging import logging_redirect_tqdm

    logger = get_logger()
    formatter = logging.Formatter(DEFAULT_LOGGING_FORMAT)
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    if level:
        logger.setLevel(level)

    return logging_redirect_tqdm([logger])

