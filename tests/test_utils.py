# coding: utf-8
import os

import pytest

from synergine2.utils import ChunkManager
from synergine2_cocos2d.exception import FileNotFound
from synergine2_cocos2d.util import PathManager
from synergine2_cocos2d.util import get_map_file_path_from_dir
from tests import BaseTest


class TestUtils(BaseTest):
    def test_chunk_manager_round(self):
        chunk_manager = ChunkManager(4)
        data = list(range(100))

        chunks = chunk_manager.make_chunks(data)

        assert len(chunks) == 4
        for chunk in chunks:
            assert len(chunk) == 25

    def test_chunk_manager_not_round(self):
        chunk_manager = ChunkManager(4)
        data = list(range(101))

        chunks = chunk_manager.make_chunks(data)

        assert len(chunks) == 4
        for chunk_number, chunk in enumerate(chunks):
            if chunk_number == 3:
                assert len(chunk) == 26
            else:
                assert len(chunk) == 25

    def test_path_manager(self):
        path_manager = PathManager(['tests/fixtures/some_media'])
        # file in thirst dir found
        assert 'tests/fixtures/some_media/foo.txt' == path_manager.path('foo.txt')
        # a non existing file is not found
        with pytest.raises(FileNotFound):
            path_manager.path('UNKNOWN')
        # if add a folder to path manager paths
        path_manager.add_included_path('tests/fixtures/some_media2')
        # it is prior on path finding
        assert 'tests/fixtures/some_media2/foo.txt' == path_manager.path('foo.txt')

    def test_get_map_file_path_from_dir(self):
        assert get_map_file_path_from_dir('map/003') == 'map/003/003.tmx'
        assert get_map_file_path_from_dir('map/003/') == 'map/003/003.tmx'
