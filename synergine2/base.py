# coding: utf-8


class BaseObject(object):
    def repr_debug(self) -> str:
        return type(self).__name__


class IdentifiedObject(BaseObject):
    def __init__(self, *args, **kwargs):
        self._id = id(self)

    @property
    def id(self) -> int:
        return self._id
