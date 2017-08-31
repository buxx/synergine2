# coding: utf-8
import typing

import pylibmc

from synergine2.exceptions import SynergineException


class SharedDataManager(object):
    """
    This object is designed to own shared memory between processes. It must be feed (with set method) before
    start of processes. Processes will only be able to access shared memory filled here before start.
    """
    def __init__(self):
        self._mc = pylibmc.Client(['127.0.0.1'], binary=True, behaviors={"tcp_nodelay": True, "ketama": True})

    def set(self, key: str, value: typing.Any) -> None:
        self._mc.set(key, value)

    def get(self, key) -> typing.Any:
        return self._mc.get(key)

    def create(
        self,
        key: str,
        value,
        indexes=None,
    ):
        def get_key(obj):
            return key

        def get_key_with_id(obj):
            return key.format(id=obj.id)

        if '{id}' in key:
            key_formatter = get_key_with_id
        else:
            self.set(key, value)
            key_formatter = get_key

        def fget(self_):
            return self.get(key)

        def fset(self_, value_):
            self.set(key_formatter(self_), value_)

        def fdel(self_):
            raise SynergineException('You cannot delete a shared data')

        shared_property = property(
            fget=fget,
            fset=fset,
            fdel=fdel,
        )

        return shared_property

