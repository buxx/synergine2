# coding: utf-8
import pickle
import typing

import redis

from synergine2.base import IdentifiedObject
from synergine2.exceptions import SynergineException
from synergine2.exceptions import UnknownSharedData


class NoSharedDataInstance(SynergineException):
    pass


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


class SharedData(object):
    def __init__(
        self,
        key: str,
        self_type: bool=False,
        default: typing.Any=None,
    ) -> None:
        """
        :param key: shared data key
        :param self_type: if it is a magic shared data where real key is association of key and instance id
        :param default: default/initial value to shared data. Can be a callable to return list or dict
        """
        self._key = key
        self.self_type = self_type
        self._default = default
        self.is_special_type = isinstance(self.default_value, (list, dict))
        self.type = type(self.default_value)
        if self.is_special_type:
            if isinstance(self.default_value, list):
                self.special_type = TrackedList
            elif isinstance(self.default_value, dict):
                self.special_type = TrackedDict
            else:
                raise NotImplementedError()

    def get_final_key(self, instance: IdentifiedObject) -> str:
        if self.self_type:
            return '{}_{}'.format(instance.id, self._key)
        return self._key

    @property
    def default_value(self) -> typing.Any:
        if callable(self._default):
            return self._default()

        return self._default


class TrackedDict(dict):
    base = dict

    def __init__(self, seq=None, **kwargs):
        self.shared_data = kwargs.pop('shared_data')
        self.shared = kwargs.pop('shared')
        self.instance = kwargs.pop('instance')
        super().__init__(seq, **kwargs)

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self.shared.set(self.shared_data.get_final_key(self.instance), dict(self))

    def setdefault(self, k, d=None):
        v = super().setdefault(k, d)
        self.shared.set(self.shared_data.get_final_key(self.instance), dict(self))
        return v
    # TODO: Cover all methods


class TrackedList(list):
    base = list

    def __init__(self, seq=(), **kwargs):
        self.shared_data = kwargs.pop('shared_data')
        self.shared = kwargs.pop('shared')
        self.instance = kwargs.pop('instance')
        super().__init__(seq)

    def append(self, p_object):
        super().append(p_object)
        self.shared.set(self.shared_data.get_final_key(self.instance), list(self))

    def remove(self, object_):
        super().remove(object_)
        self.shared.set(self.shared_data.get_final_key(self.instance), list(self))

    def extend(self, iterable) -> None:
        super().extend(iterable)
        self.shared.set(self.shared_data.get_final_key(self.instance), list(self))

    # TODO: Cover all methods


class SharedDataManager(object):
    """
    This object is designed to own shared memory between processes. It must be feed (with set method) before
    start of processes. Processes will only be able to access shared memory filled here before start.
    """
    def __init__(self, clear: bool=True):
        self._r = redis.StrictRedis(host='localhost', port=6379, db=0)  # TODO: configs

        self._shared_data_list = []  # type: typing.List[SharedData]

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

    def purge_data(self):
        self._data = {}

    def set(self, key: str, value: typing.Any) -> None:
        # FIXME: Called tout le temps !
        self._data[key] = value
        self._modified_keys.add(key)

    def get(self, key: str) -> typing.Any:
        try:
            return self._data[key]
        except KeyError:
            database_value = self._r.get(key)
            if database_value is None:
                # We not allow None value storage
                raise UnknownSharedData('No shared data for key "{}"'.format(key))
            value = pickle.loads(database_value)
            self._data[key] = value

        return self._data[key]

    def commit(self) -> None:
        for key in self._modified_keys:
            value = self.get(key)
            self._r.set(key, pickle.dumps(value))

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

    def create_self(
        self,
        key: str,
        default: typing.Any,
        indexes: typing.List[SharedDataIndex]=None,
    ):
        return self.create(key, self_type=True, value=default, indexes=indexes)

    def create(
        self,
        key: str,
        value: typing.Any,
        self_type: bool=False,
        indexes: typing.List[SharedDataIndex]=None,
    ):
        # TODO: Store all keys and forbid re-use one
        indexes = indexes or []
        shared_data = SharedData(
            key=key,
            self_type=self_type,
            default=value,
        )
        self._shared_data_list.append(shared_data)

        def fget(instance):
            final_key = shared_data.get_final_key(instance)

            try:
                value_ = self.get(final_key)
                if not shared_data.is_special_type:
                    return value_
                else:
                    return shared_data.special_type(value_, shared_data=shared_data, shared=self, instance=instance)

            except UnknownSharedData:
                # If no data in database, value for this shared_data have been never set
                self.set(final_key, shared_data.default_value)
                self._default_values[final_key] = shared_data.default_value
                return self.get(final_key)

        def fset(instance, value_):
            final_key = shared_data.get_final_key(instance)

            try:
                previous_value = self.get(final_key)
                for index in indexes:
                    index.remove(previous_value)
            except UnknownSharedData:
                pass  # If no shared data, no previous value to remove

            if not shared_data.is_special_type:
                self.set(final_key, value_)
            else:
                self.set(final_key, shared_data.type(value_))

            for index in indexes:
                index.add(value_)

        def fdel(self_):
            raise SynergineException('You cannot delete a shared data: not implemented yet')

        shared_property = property(
            fget=fget,
            fset=fset,
            fdel=fdel,
        )

        # A simple shared data can be set now because no need to build key with instance id
        if not self_type:
            self.set(key, shared_data.default_value)
            self._default_values[key] = shared_data.default_value

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
