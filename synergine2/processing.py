import types
from multiprocessing import Process
from multiprocessing import Manager

from synergine2.utils import ChunkManager


class ProcessManager(object):
    def __init__(
            self,
            process_count: int,
            chunk_manager: ChunkManager,
    ):
        self._process_count = process_count
        self._chunk_manager = chunk_manager

    def chunk_and_execute_jobs(self, data: list, job_maker: types.FunctionType) -> list:
        with Manager() as manager:
            processes = list()
            chunks = self._chunk_manager.make_chunks(data)
            results = manager.dict()

            for process_number in range(self._process_count):
                processes.append(Process(
                    target=self._job_maker_wrapper,
                    args=(
                        process_number,
                        chunks[process_number],
                        results,
                        job_maker,
                    )
                ))

            for process in processes:
                process.start()

            for process in processes:
                process.join()

            return results.values()

    def execute_jobs(self, data: object, job_maker: types.FunctionType) -> list:
        with Manager() as manager:
            processes = list()
            results = manager.dict()

            for process_number in range(self._process_count):
                processes.append(Process(
                    target=self._job_maker_wrapper,
                    args=(
                        process_number,
                        data,
                        results,
                        job_maker,
                    )
                ))

            for process in processes:
                process.start()

            for process in processes:
                process.join()

            return results.values()

    def _job_maker_wrapper(
            self,
            process_number: int,
            data: list,
            results: dict,
            job_maker: types.FunctionType,
    ):
        results[process_number] = job_maker(data, process_number, self._process_count)
