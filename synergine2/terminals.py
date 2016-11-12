from multiprocessing import Queue

from multiprocessing import Process
from queue import Empty

import time

STOP_SIGNAL = '__STOP_SIGNAL__'


class TerminalPackage(object):
    def __init__(self, value):
        self._value = value

    @property
    def value(self):
        return self._value


class Terminal(object):
    """Default behaviour is to do nothing.
    DEFAULT_SLEEP is sleep time between each queue read"""
    DEFAULT_SLEEP = 1

    def __init__(self):
        self._input_queue = None
        self._output_queue = None
        self._stop_required = False

    def start(self, input_queue: Queue, output_queue: Queue) -> None:
        self._input_queue = input_queue
        self._output_queue = output_queue
        self.run()

    def run(self):
        """
        Override this method to create your daemon terminal
        """
        while self.read():
            time.sleep(self.DEFAULT_SLEEP)

    def read(self):
        while True:
            try:
                package = self._input_queue.get(block=False, timeout=None)
                if package == STOP_SIGNAL:
                    self._stop_required = True
                    return False

                self.receive(package)
            except Empty:
                return True  # Finished to read Queue

    def receive(self, package: TerminalPackage):
        raise NotImplementedError()

    def send(self, package: TerminalPackage):
        self._output_queue.put(package)


class TerminalManager(object):
    def __init__(self, terminals: [Terminal]):
        self._terminals = terminals
        self._outputs_queues = []
        self._inputs_queues = []

    def start(self) -> None:
        for terminal in self._terminals:
            output_queue = Queue()
            self._outputs_queues.append(output_queue)

            input_queue = Queue()
            self._inputs_queues.append(input_queue)

            process = Process(target=terminal.start, kwargs=dict(
                input_queue=output_queue,
                output_queue=input_queue,
            ))
            process.start()

    def stop(self):
        for output_queue in self._outputs_queues:
            output_queue.put(STOP_SIGNAL)

    def send(self, package: TerminalPackage):
        for output_queue in self._outputs_queues:
            output_queue.put(package)

    def receive(self) -> []:
        packages = []
        for input_queue in self._inputs_queues:
            try:
                while True:
                    packages.append(input_queue.get(block=False, timeout=None))
            except Empty:
                pass  # Queue is empty

        return packages
