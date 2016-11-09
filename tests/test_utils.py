from synergine2.utils import ChunkManager
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
