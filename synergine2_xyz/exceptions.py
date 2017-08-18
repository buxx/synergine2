# coding: utf-8
from synergine2.exceptions import SynergineException


class XYZException(SynergineException):
    pass


class MapException(XYZException):
    pass


class ImproperlyConfiguredMap(MapException):
    pass
