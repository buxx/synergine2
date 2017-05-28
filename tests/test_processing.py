# coding: utf-8
import os
import psutil

from synergine2.processing import ProcessManager
from synergine2.utils import ChunkManager
from tests import BaseTest

available_cores = len(psutil.Process().cpu_affinity())


class MyFakeClass(object):
    def __init__(self, value):
        self.value = value


class TestProcessing(BaseTest):
    def make_job_with_scalar(
            self,
            data_chunk: list,
            process_number: int,
            process_count: int,
    ) -> tuple:
        current_pid = os.getpid()
        result = sum(data_chunk)
        return current_pid, result

    def make_job_with_object(
            self,
            data_chunk: list,
            process_number: int,
            process_count: int,
    ) -> tuple:
        current_pid = os.getpid()
        data = [o.value for o in data_chunk]
        result = sum(data)
        return current_pid, MyFakeClass(result)

    def test_parallel_jobs_with_scalar(self):
        chunk_manager = ChunkManager(available_cores)
        process_manager = ProcessManager(
            process_count=available_cores,
            chunk_manager=chunk_manager,
        )

        data = list(range(100))
        process_id_list = []
        final_result = 0

        results = process_manager.chunk_and_execute_jobs(
            data,
            job_maker=self.make_job_with_scalar,
        )

        for process_id, result in results:
            final_result += result
            process_id_list.append(process_id)

        # Goal is 4950
        assert final_result == 4950

    def test_non_parallel_jobs_with_scalar(self):
        chunk_manager = ChunkManager(1)
        process_manager = ProcessManager(
            process_count=1,
            chunk_manager=chunk_manager,
        )

        data = list(range(100))
        results = process_manager.chunk_and_execute_jobs(
            data,
            job_maker=self.make_job_with_scalar,
        )
        process_id, final_result = results[0]

        assert len(results) == 1
        assert process_id == os.getpid()
        assert final_result == 4950

    def test_parallel_jobs_with_objects(self):
        chunk_manager = ChunkManager(available_cores)
        process_manager = ProcessManager(
            process_count=available_cores,
            chunk_manager=chunk_manager,
        )

        data = [MyFakeClass(v) for v in range(100)]
        process_id_list = []
        final_result = 0

        results = process_manager.chunk_and_execute_jobs(
            data,
            job_maker=self.make_job_with_object,
        )

        for process_id, result_object in results:
            final_result += result_object.value
            process_id_list.append(process_id)

        # Goal is 4950
        assert final_result == 4950
