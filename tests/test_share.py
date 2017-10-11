# coding: utf-8
import pickle

import pytest

from synergine2.base import IdentifiedObject
from synergine2.exceptions import UnknownSharedData
from synergine2 import share
from tests import BaseTest


class TestShare(BaseTest):
    def test_simple_share_with_class(self):
        shared = share.SharedDataManager()

        class Foo(object):
            counter = shared.create('counter', 0)

        foo = Foo()
        foo.counter = 42

        assert shared.get('counter') == 42

        foo.counter = 48

        assert shared.get('counter') == 48

    def test_refresh_without_commit(self):
        shared = share.SharedDataManager()

        class Foo(object):
            counter = shared.create('counter', 0)

        foo = Foo()
        foo.counter = 42

        assert shared.get('counter') == 42

        shared.refresh()
        with pytest.raises(UnknownSharedData):
            shared.get('counter')

    def test_commit(self):
        shared = share.SharedDataManager()

        class Foo(object):
            counter = shared.create('counter', 0)

        foo = Foo()
        foo.counter = 42

        assert shared.get('counter') == 42

        shared.commit()
        assert shared.get('counter') == 42

    def test_commit_then_refresh(self):
        shared = share.SharedDataManager()

        class Foo(object):
            counter = shared.create('counter', 0)

        foo = Foo()
        foo.counter = 42

        assert shared.get('counter') == 42

        shared.commit()
        shared.refresh()
        assert shared.get('counter') == 42

    def test_position_index(self):
        class ListIndex(share.SharedDataIndex):
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

        shared = share.SharedDataManager()

        class Foo(IdentifiedObject):
            position = shared.create_self(
                'position',
                (0, 0, 0),
                indexes=[shared.make_index(ListIndex, 'positions')],
            )

        with pytest.raises(UnknownSharedData):
            shared.get('positions')

        foo = Foo()
        foo.position = (0, 1, 2)

        assert shared.get('{}_position'.format(foo.id)) == (0, 1, 2)
        assert shared.get('positions') == [(0, 1, 2)]

        foo2 = Foo()
        foo2.position = (3, 4, 5)

        assert shared.get('{}_position'.format(foo.id)) == (0, 1, 2)
        assert shared.get('{}_position'.format(foo2.id)) == (3, 4, 5)
        assert shared.get('positions') == [(0, 1, 2), (3, 4, 5)]

        foo2.position = (6, 7, 8)
        assert shared.get('{}_position'.format(foo2.id)) == (6, 7, 8)
        assert shared.get('positions') == [(0, 1, 2), (6, 7, 8)]

    def test_auto_self_shared_data(self):
        shared = share.SharedDataManager()

        class MySubject(IdentifiedObject):
            age = shared.create_self('age', 0)

            @property
            def id(self):
                return id(self)

        subject = MySubject()
        assert subject.age == 0

    def test_auto_self_shared_data_with_callable(self):
        shared = share.SharedDataManager()

        class MySubject(IdentifiedObject):
            colors = shared.create_self('colors', lambda: [])

            @property
            def id(self):
                return id(self)

        subjecta = MySubject()
        subjectb = MySubject()

        assert subjecta.colors == []
        assert subjectb.colors == []

        subjecta.colors = ['toto']
        subjectb.colors = ['tata']

        assert subjecta.colors == ['toto']
        assert subjectb.colors == ['tata']

    def test_update_self_dict_with_pointer(self):
        shared = share.SharedDataManager()

        class Foo(IdentifiedObject):
            data = shared.create_self('data', lambda: {})

        foo = Foo()
        foo.data = {'foo': 'bar'}

        assert foo.data == {'foo': 'bar'}

        foo.data['foo'] = 'buz'
        # In this case local data is used
        assert foo.data == {'foo': 'buz'}

        shared.commit()
        shared.purge_data()

        # In this case, "data" key was pending and has been commit
        assert foo.data == {'foo': 'buz'}

        # In this case "data" key was NOT pending and has not been commit
        foo.data['foo'] = 'bAz'
        shared.commit()
        shared.purge_data()

        assert foo.data == {'foo': 'bAz'}

    def test_update_self_list_with_pointer(self):
        shared = share.SharedDataManager()

        class Foo(IdentifiedObject):
            data = shared.create_self('data', [])

        foo = Foo()
        foo.data = ['foo']

        assert foo.data == ['foo']

        foo.data.append('bar')
        assert foo.data == ['foo', 'bar']

        shared.commit()
        assert foo.data == ['foo', 'bar']

        foo.data.append('bAr')
        shared.commit()
        assert foo.data == ['foo', 'bar', 'bAr']

    def test_update_list_with_pointer(self):
        shared = share.SharedDataManager()

        class Foo(IdentifiedObject):
            data = shared.create('data', [])

        foo = Foo()
        foo.data = ['foo']

        assert foo.data == ['foo']
        assert shared.get('data') == ['foo']

        foo.data.append('bar')
        assert shared.get('data') == ['foo', 'bar']

    def test_update_dict_with_pointer(self):
        shared = share.SharedDataManager()

        class Foo(IdentifiedObject):
            data = shared.create('data', lambda: {})

        foo = Foo()
        foo.data = {'foo': 'bar'}

        assert shared.get('data') == {'foo': 'bar'}

        foo.data['foo'] = 'buz'
        # In this case local data is used
        assert shared.get('data') == {'foo': 'buz'}


class TestIndexes(BaseTest):
    def test_list_index(self):
        shared = share.SharedDataManager()

        class Foo(IdentifiedObject):
            position = shared.create_self(
                'position',
                (0, 0, 0),
                indexes=[shared.make_index(share.ListIndex, 'positions')],
            )

        with pytest.raises(UnknownSharedData):
            shared.get('positions')

        foo = Foo()
        foo.position = (0, 1, 2)

        assert shared.get('{}_position'.format(foo.id)) == (0, 1, 2)
        assert shared.get('positions') == [(0, 1, 2)]

        foo2 = Foo()
        foo2.position = (3, 4, 5)

        assert shared.get('{}_position'.format(foo.id)) == (0, 1, 2)
        assert shared.get('{}_position'.format(foo2.id)) == (3, 4, 5)
        assert shared.get('positions') == [(0, 1, 2), (3, 4, 5)]

        foo2.position = (6, 7, 8)
        assert shared.get('{}_position'.format(foo2.id)) == (6, 7, 8)
        assert shared.get('positions') == [(0, 1, 2), (6, 7, 8)]
