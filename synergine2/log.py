# coding: utf-8
import logging

import sys
import typing


class SynergineLogger(logging.getLoggerClass()):
    @property
    def is_debug(self) -> bool:
        return self.isEnabledFor(logging.DEBUG)


def get_default_logger(name: str='synergine', level: int=logging.ERROR) -> SynergineLogger:
    """
    WARNING: Set global logging Logger class to SynergineLogger
    """
    logging.setLoggerClass(SynergineLogger)
    logger = logging.getLogger(name)
    logger = typing.cast(SynergineLogger, logger)
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s|%(name)s|%(process)d|%(levelname)s: %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(level)

    return logger
