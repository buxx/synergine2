import typing
from contextlib import contextmanager

import time

from synergine2.base import BaseObject


class ChunkManager(BaseObject):
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


class ElapsedTime(object):
    def __init__(self, start_time: float) -> None:
        self.start_time = start_time
        self.end_time = None

    def get_final_time(self) -> float:
        assert self.end_time
        return self.end_time - self.start_time

    def get_time(self) -> float:
        return time.time() - self.start_time


@contextmanager
def time_it() -> typing.Generator[ElapsedTime, None, None]:
    elapsed_time = ElapsedTime(time.time())
    try:
        yield elapsed_time
    finally:
        elapsed_time.end_time = time.time()
