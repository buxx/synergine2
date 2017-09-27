# coding: utf-8
import pickle
import typing

import collections
import redis

from synergine2.exceptions import SynergineException
from synergine2.exceptions import UnknownSharedData


class SharedDataIndex(object):
    def __init__(
        self,
        shared_data_manager: 'SharedDataManager',
        key: str,
    ) -> None:
        self.shared_data_manager = shared_data_manager
        self.key = key

    def add(self, value: typing.Any) -> None:
        raise NotImplementedError()

    def remove(self, value: typing.Any) -> None:
        raise NotImplementedError()


class TrackedDict(dict):
    base = dict

    def __init__(self, seq=None, **kwargs):
        self.key = kwargs.pop('key')
        self.shared = kwargs.pop('shared')
        super().__init__(seq, **kwargs)

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self.shared.set(self.key, dict(self))

    def setdefault(self, k, d=None):
        v = super().setdefault(k, d)
        self.shared.set(self.key, dict(self))
        return v
    # TODO: Cover all methods


class TrackedList(list):
    base = list

    def __init__(self, seq=(), **kwargs):
        self.key = kwargs.pop('key')
        self.shared = kwargs.pop('shared')
        super().__init__(seq)

    def append(self, p_object):
        super().append(p_object)
        self.shared.set(self.key, list(self))

    # TODO: Cover all methods


class SharedDataManager(object):
    """
    This object is designed to own shared memory between processes. It must be feed (with set method) before
    start of processes. Processes will only be able to access shared memory filled here before start.
    """
    def __init__(self, clear: bool=True):
        self._r = redis.StrictRedis(host='localhost', port=6379, db=0)  # TODO: configs

        self._data = {}
        self._modified_keys = set()
        self._default_values = {}
        self._special_types = {}  # type: typing.Dict[str, typing.Union[typing.Type[TrackedDict], typing.Type[TrackedList]]]  # nopep8

        if clear:
            self.clear()

    def clear(self) -> None:
        self._r.flushdb()
        self._data = {}
        self._modified_keys = set()

    def reset(self) -> None:
        for key, value in self._default_values.items():
            self.set(key, value)
        self.commit()
        self._data = {}

    def set(self, key: str, value: typing.Any) -> None:
        try:
            special_type = self._special_types[key]
            value = special_type(value, key=key, shared=self)
        except KeyError:
            pass

        self._data[key] = value
        self._modified_keys.add(key)

    def get(self, *key_args: typing.Union[str, float, int]) -> typing.Any:
        key = '_'.join([str(v) for v in key_args])

        try:
            return self._data[key]
        except KeyError:
            b_value = self._r.get(key)
            if b_value is None:
                # We not allow None value storage
                raise UnknownSharedData('No shared data for key "{}"'.format(key))

            value = pickle.loads(b_value)
            special_type = None

            try:
                special_type = self._special_types[key]
            except KeyError:
                pass

            if special_type:
                self._data[key] = special_type(value, key=key, shared=self)
            else:
                self._data[key] = value

        return self._data[key]

    def commit(self) -> None:
        for key in self._modified_keys:
            try:
                special_type = self._special_types[key]
                value = special_type.base(self.get(key))
                self._r.set(key, pickle.dumps(value))
            except KeyError:
                self._r.set(key, pickle.dumps(self.get(key)))
        self._modified_keys = set()

    def refresh(self) -> None:
        self._data = {}

    def make_index(
        self,
        shared_data_index_class: typing.Type[SharedDataIndex],
        key: str,
        *args: typing.Any,
        **kwargs: typing.Any
    ) -> SharedDataIndex:
        return shared_data_index_class(self, key, *args, **kwargs)

    def create(
        self,
        key_args: typing.Union[str, typing.List[typing.Union[str, int, float]]],
        value: typing.Any,
        indexes: typing.List[SharedDataIndex]=None,
    ):
        key = key_args
        if not isinstance(key, str):
            key = '_'.join(key_args)
        indexes = indexes or []

        if type(value) is dict:
            value = TrackedDict(value, key=key, shared=shared)
            self._special_types[key] = TrackedDict
        elif type(value) is list:
            value = TrackedList(value, key=key, shared=shared)
            self._special_types[key] = TrackedList

        def get_key(obj):
            return key

        def get_key_with_id(obj):
            return key.format(id=obj.id)

        if '{id}' in key:
            key_formatter = get_key_with_id
        else:
            self.set(key, value)
            self._default_values[key] = value
            key_formatter = get_key

        def fget(self_):
            return self.get(key)

        def fset(self_, value_):
            try:
                previous_value = self.get(key_formatter(self_))
                for index in indexes:
                    index.remove(previous_value)
            except UnknownSharedData:
                pass  # If no shared data, no previous value to remove

            self.set(key_formatter(self_), value_)

            for index in indexes:
                index.add(value_)

        def fdel(self_):
            raise SynergineException('You cannot delete a shared data')

        shared_property = property(
            fget=fget,
            fset=fset,
            fdel=fdel,
        )

        return shared_property

# TODO: Does exist a way to permit overload of SharedDataManager class ?
shared = SharedDataManager()


class ListIndex(SharedDataIndex):
    def add(self, value):
        try:
            values = self.shared_data_manager.get(self.key)
        except UnknownSharedData:
            values = []

        values.append(value)
        self.shared_data_manager.set(self.key, values)

    def remove(self, value):
        values = self.shared_data_manager.get(self.key)
        values.remove(value)
        self.shared_data_manager.set(self.key, values)
