# coding: utf-8
import pytest

from synergine2.exceptions import UnknownSharedData
from synergine2.share import SharedDataManager
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
                (0, 0, 0),
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

    def test_indexes(self):
        pass
