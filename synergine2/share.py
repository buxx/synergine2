# coding: utf-8
import pickle
import typing

import redis

from synergine2.exceptions import SynergineException


class SharedDataManager(object):
    """
    This object is designed to own shared memory between processes. It must be feed (with set method) before
    start of processes. Processes will only be able to access shared memory filled here before start.
    """
    def __init__(self):
        self._r = redis.StrictRedis(host='localhost', port=6379, db=0)  # TODO: configs
        # TODO: Il faut écrire dans REDIS que lorsque l'on veut passer à l'étape processes, genre de commit
        # sinon on va ecrire dans redis a chaque fois qu'on modifie une shared data c'est pas optimal.

    def set(self, key: str, value: typing.Any) -> None:
        self._r.set(key, pickle.dumps(value))

    def get(self, key) -> typing.Any:
        return pickle.loads(self._r.get(key))

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

