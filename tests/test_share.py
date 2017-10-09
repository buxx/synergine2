# coding: utf-8
import pickle

import pytest

from synergine2.exceptions import UnknownSharedData
from synergine2 import share
from tests import BaseTest


class TestShare(BaseTest):
    def test_simple_share_with_class(self):
        shared = share.SharedDataManager()

        class Foo(object):
            counter = shared.create('counter', value=0)

        foo = Foo()
        foo.counter = 42

        assert shared.get('counter') == 42

        foo.counter = 48

        assert shared.get('counter') == 48

    def test_default_value(self):
        shared = share.SharedDataManager()

        class Foo(object):
            counter = shared.create('counter', 0)

        foo = Foo()
        foo.counter = 42

        assert shared.get('counter') == 42

        foo.counter = 48

        assert shared.get('counter') == 48

    def test_dynamic_key(self):
        shared = share.SharedDataManager()

        class Foo(object):
            counter = shared.create(
                ['{id}', 'counter'],
                value=0,
                indexes=[],
            )

            @property
            def id(self):
                return id(self)

        foo = Foo()
        foo.counter = 42

        assert shared.get(foo.id, 'counter') == 42

        foo.counter = 48

        assert shared.get(foo.id, 'counter') == 48

    def test_multiple_uses(self):
        shared = share.SharedDataManager()

        class Foo(object):
            position = shared.create(
                '{id}_position',
                (0, 0, 0),
                indexes=[],
            )

            @property
            def id(self):
                return id(self)

        foo = Foo()
        foo.position = (0, 1, 2)

        assert shared.get('{}_position'.format(foo.id)) == (0, 1, 2)

        foo2 = Foo()
        foo2.position = (3, 4, 5)

        assert shared.get('{}_position'.format(foo.id)) == (0, 1, 2)
        assert shared.get('{}_position'.format(foo2.id)) == (3, 4, 5)

    def test_update_dict_with_pointer(self):
        shared = share.SharedDataManager()

        class Foo(object):
            data = shared.create('data', {})

        foo = Foo()
        foo.data = {'foo': 'bar'}

        assert shared.get('data') == {'foo': 'bar'}

        foo.data['foo'] = 'buz'
        assert shared.get('data') == {'foo': 'buz'}

        shared.commit()
        assert shared.get('data') == {'foo': 'buz'}
        assert pickle.loads(shared._r.get('data')) == {'foo': 'buz'}

        foo.data['foo'] = 'bAz'
        shared.commit()
        assert shared.get('data') == {'foo': 'bAz'}
        assert pickle.loads(shared._r.get('data')) == {'foo': 'bAz'}

    def test_update_list_with_pointer(self):
        shared = share.SharedDataManager()

        class Foo(object):
            data = shared.create('data', [])

        foo = Foo()
        foo.data = ['foo']

        assert shared.get('data') == ['foo']

        foo.data.append('bar')
        assert shared.get('data') == ['foo', 'bar']

        shared.commit()
        assert shared.get('data') == ['foo', 'bar']
        assert pickle.loads(shared._r.get('data')) == ['foo', 'bar']

        foo.data.append('bAr')
        shared.commit()
        assert shared.get('data') == ['foo', 'bar', 'bAr']
        assert pickle.loads(shared._r.get('data')) == ['foo', 'bar', 'bAr']

    def test_update_list_with_pointer__composite_key(self):
        shared = share.SharedDataManager()

        class Foo(object):
            data = shared.create(['{id}', 'data'], [])

            def __init__(self):
                self.id = id(self)

        foo = Foo()
        foo.data = ['foo']

        assert shared.get(str(id(foo)) + '_data') == ['foo']

        foo.data.append('bar')
        assert shared.get(str(id(foo)) + '_data') == ['foo', 'bar']

        shared.commit()
        assert shared.get(str(id(foo)) + '_data') == ['foo', 'bar']
        assert pickle.loads(shared._r.get(str(id(foo)) + '_data')) == ['foo', 'bar']

        foo.data.append('bAr')
        shared.commit()
        assert shared.get(str(id(foo)) + '_data') == ['foo', 'bar', 'bAr']
        assert pickle.loads(shared._r.get(str(id(foo)) + '_data')) == ['foo', 'bar', 'bAr']

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

        class Foo(object):
            position = shared.create(
                '{id}_position',
                (0, 0, 0),
                indexes=[shared.make_index(ListIndex, 'positions')],
            )

            @property
            def id(self):
                return id(self)

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


class TestIndexes(BaseTest):
    def test_list_index(self):
        shared = share.SharedDataManager()

        class Foo(object):
            position = shared.create(
                '{id}_position',
                (0, 0, 0),
                indexes=[shared.make_index(share.ListIndex, 'positions')],
            )

            @property
            def id(self):
                return id(self)

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
