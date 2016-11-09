import os

from synergine2.processing import ProcessManager
from synergine2.utils import ChunkManager
from tests import BaseTest


class TestProcessing(BaseTest):
    @staticmethod
    def _make_job(data_chunk: list) -> tuple:
        current_pid = os.getpid()
        result = sum(data_chunk)
        return current_pid, result

    def test_parallel_jobs(self):
        chunk_manager = ChunkManager(4)
        process_manager = ProcessManager(
            process_count=4,
            chunk_manager=chunk_manager,
            job_maker=self._make_job,
        )

        data = list(range(100))
        process_id_list = []
        final_result = 0

        results = process_manager.execute_jobs(data)

        for process_id, result in results:
            final_result += result
            process_id_list.append(process_id)

        # Test each process ids are differents
        assert sorted(process_id_list) == \
            sorted(list(set(process_id_list)))

        # Goal is 4950
        assert final_result == 4950
