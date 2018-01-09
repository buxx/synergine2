# coding: utf-8
from synergine2.config import Config
from synergine2.processing import ProcessManager

import pytest


@pytest.fixture
def do_nothing_process_manager() -> ProcessManager:
    return ProcessManager(
        Config(),
        process_count=0,
        job=lambda: None,
    )
