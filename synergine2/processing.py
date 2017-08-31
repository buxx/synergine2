# coding: utf-8
import typing
from multiprocessing import Process
from multiprocessing.connection import Connection
from multiprocessing.connection import Pipe

from synergine2.base import BaseObject
from synergine2.config import Config
from synergine2.share import SharedDataManager

STOP = '__STOP__'

# global shared manager
shared_data = SharedDataManager()


# TODO: se jobs
class Job(object):
    pass


class Worker(object):
    def __init__(
        self,
        config: Config,
        real_job: typing.Callable[..., typing.Any],
    ) -> None:
        self.config = config

        local_read_pipe, local_write_pipe = Pipe(duplex=False)
        process_read_pipe, process_write_pipe = Pipe(duplex=False)

        self.local_read_pipe = local_read_pipe  # type: Connection
        self.local_write_pipe = local_write_pipe  # type: Connection
        self.process_read_pipe = process_read_pipe  # type: Connection
        self.process_write_pipe = process_write_pipe  # type: Connection

        self.real_job = real_job
        self.process = Process(
            target=self.work,
            args=(
                self.local_write_pipe,
                self.process_read_pipe,
            )
        )
        self.db = None  # type: RedisDatabase
        self.process.start()

    def work(self, *args, **kwargs):
        while True:
            message = self.process_read_pipe.recv()
            if message == STOP:
                return

            result = self.real_job(message)
            self.local_write_pipe.send(result)


class ProcessManager(BaseObject):
    def __init__(
            self,
            config: Config,
            process_count: int,
            job: typing.Callable[..., typing.Any],
    ) -> None:
        self.config = config
        self._process_count = process_count
        self.workers = []
        self.start_workers(process_count, job)

    def start_workers(self, worker_count: int, job: typing.Callable[..., typing.Any]) -> None:
        assert not self.workers
        for i in range(worker_count):
            self.workers.append(Worker(self.config, job))

    def make_them_work(self, message: typing.Any) -> 'TODO':
        responses = []

        for worker in self.workers:
            worker.process_write_pipe.send(message)

        for worker in self.workers:
            responses.append(worker.local_read_pipe.recv())

        return responses

    def terminate(self) -> None:
        for worker in self.workers:
            worker.process_write_pipe.send(STOP)

        for worker in self.workers:
            worker.process.join()

    #
    # def chunk_and_execute_jobs(self, data: list, job_maker: types.FunctionType) -> list:
    #     chunks = self._chunk_manager.make_chunks(data)
    #
    #     if self._process_count > 1:
    #         print('USE POOL')
    #         results = self.pool.starmap(job_maker, [(chunk, i, self._process_count) for i, chunk in enumerate(chunks)])
    #     else:
    #         print('USE MONO')
    #         results = [job_maker(data, 0, 1)]
    #
    #     return results
    #
    # def execute_jobs(self, data: object, job_maker: types.FunctionType) -> list:
    #     # TODO: Is there a reason to make multiprocessing here ? data is not chunked ...
    #     if self._process_count > 1:
    #         results = self.pool.starmap(job_maker, [(data, i, self._process_count) for i in range(self._process_count)])
    #     else:
    #         results = [job_maker(data, 0, 1)]
    #
    #     return results
    #
    # def __del__(self):
    #     # TODO: DEV
    #     return
    #     if self.pool:
    #         self.pool.terminate()
