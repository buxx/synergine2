import types
from multiprocessing import Process
from multiprocessing import Manager

from synergine2.utils import ChunkManager


class ProcessManager(object):
    def __init__(
            self,
            process_count: int,
            chunk_manager: ChunkManager,
            job_maker: types.FunctionType,
    ):
        self._process_count = process_count
        self._chunk_manager = chunk_manager
        self._job_maker = job_maker

    def execute_jobs(self, data: list) -> tuple:
        with Manager() as manager:
            processes = list()
            chunks = self._chunk_manager.make_chunks(data)
            results = manager.dict()

            # TODO: retrouver tests pour savoir si
            # les keeped alive sont mieux
            for process_number in range(self._process_count):
                processes.append(Process(
                    target=self._job_maker_wrapper,
                    args=(
                        process_number,
                        chunks[process_number],
                        results,
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
            chunk: list,
            results: dict,
    ):
        results[process_number] = self._job_maker(chunk)
