# coding: utf-8
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

    def test_indexes(self):
        pass
