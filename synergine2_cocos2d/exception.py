# coding: utf-8


class WorldException(Exception):
    pass


class PositionException(WorldException):
    pass


class OuterWorldPosition(PositionException):
    pass


class InteractionNotFound(Exception):
    pass
