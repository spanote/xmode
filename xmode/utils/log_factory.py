from logging import getLogger, StreamHandler


def make_basic_logger(name:str, level:int):
    log_handler = StreamHandler()
    log_handler.setLevel(level)

    logger = getLogger(name)
    logger.setLevel(level)
    logger.addHandler(log_handler)

    return logger