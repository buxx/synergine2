# coding: utf-8
import ctypes
import multiprocessing
import psutil
from multiprocessing import Manager
from multiprocessing import Array

import pytest

from synergine2.config import Config
from synergine2.processing import ProcessManager
from synergine2.share import SharedDataManager
from tests import BaseTest

available_cores = len(psutil.Process().cpu_affinity())


class MyFakeClass(object):
    def __init__(self, value):
        self.value = value


class TestProcessing(BaseTest):
    @pytest.mark.timeout(10)
    def make_job_with_scalar(
            self,
            data: list,
    ):
        result = sum(data)
        return result

    @pytest.mark.timeout(10)
    def make_job_with_object(
            self,
            data: list,
    ):
        data = [o.value for o in data]
        result = sum(data)
        return MyFakeClass(result)

    def test_parallel_jobs_with_scalar(self):
        process_manager = ProcessManager(
            config=Config({}),
            process_count=available_cores,
            job=self.make_job_with_scalar,
        )

        data = list(range(100))

        results = process_manager.make_them_work(data)
        process_manager.terminate()

        assert sum(results) == 39600

    @pytest.mark.timeout(10)
    def test_non_parallel_jobs_with_scalar(self):
        # TODO: process manager utilise actuellement un cpu quand même, changer ca
        process_manager = ProcessManager(
            config=Config({}),
            process_count=1,
            job=self.make_job_with_scalar,
        )

        data = list(range(100))
        results = process_manager.make_them_work(data)
        process_manager.terminate()
        final_result = results[0]

        assert len(results) == 1
        assert final_result == 4950

    @pytest.mark.timeout(10)
    def test_parallel_jobs_with_objects(self):
        process_manager = ProcessManager(
            config=Config({}),
            process_count=available_cores,
            job=self.make_job_with_object,
        )

        data = [MyFakeClass(v) for v in range(100)]
        final_result = 0

        results = process_manager.make_them_work(data)
        process_manager.terminate()

        for result_object in results:
            final_result += result_object.value

        assert final_result == 39600

    @pytest.mark.timeout(10)
    def test_shared_memory_with_shared_manager(self):
        shared = SharedDataManager()
        shared.set('counter', 42)

        def job(*args, **kwargs):
            counter = shared.get('counter') or 0
            return counter + 1

        process_manager = ProcessManager(
            config=Config({}),
            process_count=available_cores,
            job=job,
        )

        results = process_manager.make_them_work(None)
        process_manager.terminate()

        assert results[0] == 43

    @pytest.mark.timeout(10)
    def test_share_data_with_function(self):
        shared = SharedDataManager()

        class Foo(object):
            counter = shared.create('counter', 0)

        def job(*args, **kwargs):
            counter = shared.get('counter') or 0
            return counter + 1

        process_manager = ProcessManager(
            config=Config({}),
            process_count=available_cores,
            job=job,
        )

        foo = Foo()
        foo.counter = 42

        results = process_manager.make_them_work(None)
        assert results[0] == 43

        foo.counter = 45

        results = process_manager.make_them_work(None)
        assert results[0] == 46

        process_manager.terminate()

    @pytest.mark.timeout(10)
    def test_after_created_shared_data(self):
        shared = SharedDataManager()

        shared.set('foo_1', 0)

        def job(key):
            value = shared.get('foo_{}'.format(key)) or 0
            return value + 1

        process_manager = ProcessManager(
            config=Config({}),
            process_count=available_cores,
            job=job,
        )

        shared.set('foo_1', 42)

        results = process_manager.make_them_work('1')
        assert results[0] == 43

        shared.set('foo_2', 52)

        results = process_manager.make_them_work('2')
        assert results[0] == 53

        process_manager.terminate()
