

class ChunkManager(object):
    def __init__(self, chunks_numbers: int):
        self._chunks_numbers = chunks_numbers

    def make_chunks(self, data: list) -> list:
        i, j, x = len(data), 0, []
        for k in range(self._chunks_numbers):
            a, j = j, j + (i + k) // self._chunks_numbers
            x.append(data[a:j])
        return x
