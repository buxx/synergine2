# coding: utf-8
import logging
import sys
import typing

from synergine2.config import Config

STREAM_HANDLER_TAG = '__STREAM_HANDLER__'


class SynergineLogger(logging.getLoggerClass()):
    @property
    def is_debug(self) -> bool:
        return self.isEnabledFor(logging.DEBUG)

    def __getstate__(self):
        # Multiprocessing fail if stream handler present. Remove it if exist.
        # TODO Bug when want to store STREAM_HANDLER_TAG instead stream handler. str still in handlers after
        # __setstate__ ...
        self.handlers = []

        return self.__dict__.copy()

    def __setstate__(self, state):
        self.__dict__ = state
        # TODO: This handler is hardcoded, it must depend of real context
        self.handlers.append(logging.StreamHandler(sys.stdout))


def get_default_logger(
    name: str='synergine',
    level: int=logging.ERROR,
) -> SynergineLogger:
    """
    WARNING: Set global logging Logger class to SynergineLogger
    """
    logging.setLoggerClass(SynergineLogger)
    logger = logging.getLogger(name)
    logger = typing.cast(SynergineLogger, logger)
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        '%(asctime)s|%(name)s|%(process)d|%(levelname)s: %(message)s',
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(level)

    return logger


def get_logger(name: str, config: Config) -> SynergineLogger:
    global_logging_level = config.resolve('global.logging_level', 'ERROR')
    logger_level_str = config.resolve('global.logging.{}.level', global_logging_level)
    logger_level = logging.getLevelName(logger_level_str)
    return get_default_logger('synergine-{}'.format(name), logger_level)
