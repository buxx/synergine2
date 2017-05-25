# coding: utf-8
import types
from multiprocessing import Pool

from synergine2.utils import ChunkManager


class ProcessManager(object):
    def __init__(
            self,
            process_count: int,
            chunk_manager: ChunkManager,
    ):
        self._process_count = process_count
        self._chunk_manager = chunk_manager
        self.pool = Pool(processes=self._process_count)

    def __getstate__(self):
        self_dict = self.__dict__.copy()
        del self_dict['pool']
        return self_dict

    def chunk_and_execute_jobs(self, data: list, job_maker: types.FunctionType) -> list:
        chunks = self._chunk_manager.make_chunks(data)

        if self._process_count > 1:
            results = self.pool.starmap(job_maker, [(chunk, i, self._process_count) for i, chunk in enumerate(chunks)])
        else:
            results = [job_maker(data, 0, 1)]

        return results

    def execute_jobs(self, data: object, job_maker: types.FunctionType) -> list:
        # TODO: Is there a reason to make multiprocessing here ? data is not chunked ...
        if self._process_count > 1:
            results = self.pool.starmap(job_maker, [(data, i, self._process_count) for i in range(self._process_count)])
        else:
            results = [job_maker(data, 0, 1)]

        return results
