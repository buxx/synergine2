# coding: utf-8
from synergine2.exceptions import SynergineException


class WorldException(Exception):
    pass


class PositionException(WorldException):
    pass


class OuterWorldPosition(PositionException):
    pass


class InteractionNotFound(Exception):
    pass


class MediaException(SynergineException):
    pass


class FileNotFound(SynergineException):
    pass
