import collections
from copy import copy
from multiprocessing import Queue

from multiprocessing import Process
from queue import Empty

import time
from synergine2.simulation import Subject
from synergine2.simulation import Event

STOP_SIGNAL = '__STOP_SIGNAL__'


class TerminalPackage(object):
    def __init__(
            self,
            subjects: [Subject]=None,
            add_subjects: [Subject]=None,
            remove_subjects: [Subject]=None,
            events: [Event]=None,
            simulation_actions: [tuple]=None,
            subject_actions: [tuple]=None,
            is_cycle: bool=False,
            *args,
            **kwargs
    ):
        self.subjects = subjects
        self.add_subjects = add_subjects or []
        self.remove_subjects = remove_subjects or []
        self.events = events or []
        self.simulation_actions = simulation_actions or []
        self.subject_actions = subject_actions or []
        self.is_cycle = is_cycle


class Terminal(object):
    # Default behaviour is to do nothing.
    # DEFAULT_SLEEP is sleep time between each queue read
    default_sleep = 1
    # List of subscribed Event classes. Terminal will not receive events
    # who are not instance of listed classes
    subscribed_events = [Event]

    def __init__(self, asynchronous: bool=True):
        self._input_queue = None
        self._output_queue = None
        self._stop_required = False
        self.subjects = {}
        self.cycle_events = []
        self.event_handlers = collections.defaultdict(list)
        self.asynchronous = asynchronous

    def accept_event(self, event: Event) -> bool:
        for event_class in self.subscribed_events:
            if isinstance(event, event_class):
                return True
        return False

    def start(self, input_queue: Queue, output_queue: Queue) -> None:
        self._input_queue = input_queue
        self._output_queue = output_queue
        self.run()

    def run(self):
        """
        Override this method to create your daemon terminal
        """
        try:
            while self.read():
                time.sleep(self.default_sleep)
        except KeyboardInterrupt:
            pass

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
        self.update_with_package(package)
        # End of cycle management signal
        self.send(TerminalPackage(is_cycle=True))

    def send(self, package: TerminalPackage):
        self._output_queue.put(package)

    def register_event_handler(self, event_class, func):
        self.event_handlers[event_class].append(func)

    def update_with_package(self, package: TerminalPackage):
        if package.subjects:
            self.subjects = {s.id: s for s in package.subjects}

        for new_subject in package.add_subjects:
            self.subjects[new_subject.id] = new_subject

        for deleted_subject in package.remove_subjects:
            del self.subjects[deleted_subject.id]

        self.cycle_events = package.events
        self.execute_event_handlers(package.events)

    def execute_event_handlers(self, events: [Event]):
        for event in events:
            for event_class, handlers in self.event_handlers.items():
                if isinstance(event, event_class):
                    for handler in handlers:
                        handler(event)


class TerminalManager(object):
    def __init__(self, terminals: [Terminal]):
        self.terminals = terminals
        self.outputs_queues = {}
        self.inputs_queues = {}

    def start(self) -> None:
        for terminal in self.terminals:
            output_queue = Queue()
            self.outputs_queues[terminal] = output_queue

            input_queue = Queue()
            self.inputs_queues[terminal] = input_queue

            process = Process(target=terminal.start, kwargs=dict(
                input_queue=output_queue,
                output_queue=input_queue,
            ))
            process.start()

    def stop(self):
        for output_queue in self.outputs_queues.values():
            output_queue.put(STOP_SIGNAL)

    def send(self, package: TerminalPackage):
        for terminal, output_queue in self.outputs_queues.items():
            # Terminal maybe don't want all events, so reduce list of event
            # Thirst make a copy to personalize this package
            terminal_adapted_package = copy(package)
            # Duplicate events list to personalize it
            terminal_adapted_package.events = terminal_adapted_package.events[:]

            for package_event in terminal_adapted_package.events[:]:
                if not terminal.accept_event(package_event):
                    terminal_adapted_package.events.remove(package_event)

            output_queue.put(terminal_adapted_package)

    def receive(self) -> [TerminalPackage]:
        packages = []
        for terminal, input_queue in self.inputs_queues.items():
            # When terminal is synchronous, wait it's cycle package
            if not terminal.asynchronous:
                continue_ = True
                while continue_:
                    package = input_queue.get()
                    # In case where terminal send package before end of cycle
                    # management
                    continue_ = not package.is_cycle
                    packages.append(package)
            else:
                try:
                    while True:
                        packages.append(
                            input_queue.get(block=False, timeout=None),
                        )
                except Empty:
                    pass  # Queue is empty

        return packages
