# coding: utf-8
import pickle
import typing

import redis

from synergine2.exceptions import SynergineException
from synergine2.exceptions import UnknownSharedData


class SharedDataManager(object):
    """
    This object is designed to own shared memory between processes. It must be feed (with set method) before
    start of processes. Processes will only be able to access shared memory filled here before start.
    """
    def __init__(self, clear: bool=True):
        self._r = redis.StrictRedis(host='localhost', port=6379, db=0)  # TODO: configs

        self._data = {}
        self._modified_keys = set()

        if clear:
            self._r.flushdb()

    def set(self, key: str, value: typing.Any) -> None:
        self._data[key] = value
        self._modified_keys.add(key)

    def get(self, key) -> typing.Any:
        if key not in self._data:
            b_value = self._r.get(key)
            if b_value is None:
                # We not allow None value storage
                raise UnknownSharedData('No shared data for key "{}"'.format(key))
            self._data[key] = pickle.loads(b_value)

        return self._data[key]

    def commit(self) -> None:
        for key in self._modified_keys:
            self._r.set(key, pickle.dumps(self.get(key)))
        self._modified_keys = set()

    def refresh(self) -> None:
        self._data = {}

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

