# coding: utf-8
import pytest

from synergine2.exceptions import UnknownSharedData
from synergine2.share import SharedDataManager
from synergine2.share import SharedDataIndex
from tests import BaseTest


class TestShare(BaseTest):
    def test_simple_share_with_class(self):
        shared = SharedDataManager()

        class Foo(object):
            counter = shared.create('counter', 0)

        foo = Foo()
        foo.counter = 42

        assert shared.get('counter') == 42

        foo.counter = 48

        assert shared.get('counter') == 48

    def test_dynamic_key(self):
        shared = SharedDataManager()

        class Foo(object):
            counter = shared.create(
                '{id}_counter',
                0,
                indexes=[],
            )

            @property
            def id(self):
                return id(self)

        foo = Foo()
        foo.counter = 42

        assert shared.get('{}_counter'.format(foo.id)) == 42

        foo.counter = 48

        assert shared.get('{}_counter'.format(foo.id)) == 48

    def test_multiple_uses(self):
        shared = SharedDataManager()

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
        shared = SharedDataManager()

        class Foo(object):
            data = shared.create('data', {})

        foo = Foo()
        foo.data = {'foo': 'bar'}

        assert shared.get('data') == {'foo': 'bar'}

        foo.data['foo'] = 'buz'
        assert shared.get('data') == {'foo': 'buz'}

    def test_refresh_without_commit(self):
        shared = SharedDataManager()

        class Foo(object):
            counter = shared.create('counter', 0)

        foo = Foo()
        foo.counter = 42

        assert shared.get('counter') == 42

        shared.refresh()
        with pytest.raises(UnknownSharedData):
            shared.get('counter')

    def test_commit(self):
        shared = SharedDataManager()

        class Foo(object):
            counter = shared.create('counter', 0)

        foo = Foo()
        foo.counter = 42

        assert shared.get('counter') == 42

        shared.commit()
        assert shared.get('counter') == 42

    def test_commit_then_refresh(self):
        shared = SharedDataManager()

        class Foo(object):
            counter = shared.create('counter', 0)

        foo = Foo()
        foo.counter = 42

        assert shared.get('counter') == 42

        shared.commit()
        shared.refresh()
        assert shared.get('counter') == 42

    def test_position_index(self):
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

        shared = SharedDataManager()

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
