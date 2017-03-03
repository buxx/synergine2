# coding: utf-8


class BaseObject(object):
    def repr_debug(self) -> str:
        return type(self).__name__
