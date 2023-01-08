import logging


logger = logging.getLogger("airflow.task")


def critical(message, *args, **kwargs):
    return logger.critical(message, *args, **kwargs)


def debug(message, *args, **kwargs):
    return logger.debug(message, *args, **kwargs)


def error(message, *args, **kwargs):
    return logger.error(message, *args, **kwargs)


def info(message, *args, **kwargs):
    return logger.info(message, *args, **kwargs)


def warning(message, *args, **kwargs):
    return logger.warning(message, *args, **kwargs)
