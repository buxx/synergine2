

class ChunkManager(object):
    def __init__(self, chunks_numbers: int):
        self._chunks_numbers = chunks_numbers

    def make_chunks(self, data: list) -> list:
        if self._chunks_numbers == 1:
            return [data]

        i, j, x = len(data), 0, []
        for k in range(self._chunks_numbers):
            a, j = j, j + (i + k) // self._chunks_numbers
            x.append(data[a:j])
        return x


def get_mechanisms_classes(mechanized) -> ['Mechanisms']:
    mechanisms_classes = []
    for behaviour_class in mechanized.behaviours_classes:
        mechanisms_classes.extend(behaviour_class.use)
    return list(set(mechanisms_classes))  # Remove duplicates
