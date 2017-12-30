# coding: utf-8
import collections
import typing
from copy import copy
from multiprocessing import Queue
from multiprocessing import Process
from queue import Empty
import time

from synergine2.base import BaseObject
from synergine2.exceptions import SynergineException
from synergine2.share import shared
from synergine2.config import Config
from synergine2.log import SynergineLogger
from synergine2.simulation import Subject
from synergine2.simulation import Event

if typing.TYPE_CHECKING:
    from synergine2.core import Core

STOP_SIGNAL = '__STOP_SIGNAL__'


class TerminalPackage(BaseObject):
    """
    TODO: Update this class considering shared data across processes
    """
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

    def repr_debug(self) -> str:
        subjects = self.subjects or []
        return str(dict(
            subjects=subjects,
            add_subjects=[s.id for s in self.add_subjects],
            remove_subjects=[s.id for s in self.remove_subjects],
            events=[e.repr_debug() for e in self.events],
            simulation_actions=['{}: {}'.format(a.__class__.__name__, p) for a, p in self.simulation_actions],
            subject_actions=['{}: {}'.format(a.__class__.__name__, p) for a, p in self.subject_actions],
            is_cycle=self.is_cycle,
        ))


class Terminal(BaseObject):
    # Default behaviour is to do nothing.
    # DEFAULT_SLEEP is sleep time between each queue read
    default_sleep = 1
    # List of subscribed Event classes. Terminal will not receive events
    # who are not instance of listed classes
    subscribed_events = [Event]
    # Permit to execute terminal in main process, only one terminal can use this
    main_process = False

    def __init__(
        self,
        config: Config,
        logger: SynergineLogger,
        asynchronous: bool=True,
    ):
        self.config = config
        self.logger = logger
        self._input_queue = None
        self._output_queue = None
        self._stop_required = False
        self.subjects = {}
        self.cycle_events = []
        self.event_handlers = collections.defaultdict(list)
        self.asynchronous = asynchronous
        self.core_process = None  # type: Process

    def accept_event(self, event: Event) -> bool:
        for event_class in self.subscribed_events:
            if isinstance(event, event_class):
                return True
        return False

    def start(self, input_queue: Queue, output_queue: Queue) -> None:
        self._input_queue = input_queue
        self._output_queue = output_queue
        self.run()

    def execute_as_main_process(self, core: 'Core') -> None:
        """
        This method is called when the terminal have to be the main process. It will
        create a process with the run of core and make it's job here.
        """
        output_queue = Queue()
        input_queue = Queue()

        self.logger.info('Start core in a process')
        self.core_process = Process(target=core.run, kwargs=dict(
            from_terminal=self,
            from_terminal_input_queue=output_queue,
            from_terminal_output_queue=input_queue,
        ))
        self.core_process.start()

        # Core is started, continue this terminal job
        self.logger.info('Core started, continue terminal job')
        self.start(input_queue=input_queue, output_queue=output_queue)

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
        self.logger.debug('Read package from core')
        while True:
            try:
                package = self._input_queue.get(block=False, timeout=None)
                if package == STOP_SIGNAL:
                    self.logger.debug('Stop required')
                    self._stop_required = True
                    return False

                self.logger.debug('Package received')
                self.receive(package)
            except Empty:
                self.logger.debug('No package')
                return True  # Finished to read Queue

    def receive(self, package: TerminalPackage):
        shared.purge_data()
        self.update_with_package(package)
        # End of cycle management signal
        self.send(TerminalPackage(is_cycle=True))

    def send(self, package: TerminalPackage):
        self.logger.debug('Send package to core')
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


class TerminalManager(BaseObject):
    def __init__(
        self,
        config: Config,
        logger: SynergineLogger,
        terminals: [Terminal]
    ):
        self.config = config
        self.logger = logger
        self.terminals = terminals
        self.outputs_queues = {}
        self.inputs_queues = {}

    def get_main_process_terminal(self) -> typing.Optional[Terminal]:
        main_process_terminals = [t for t in self.terminals if t.main_process]
        if main_process_terminals:
            if len(main_process_terminals) > 1:
                raise SynergineException('There is more one main process terminal !')
            return main_process_terminals[0]
        return None

    def start(self) -> None:
        self.logger.info('Start terminals')
        # We exclude here terminal who is run from main process
        terminals = [t for t in self.terminals if not t.main_process]
        for terminal in terminals:
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
        self.logger.info('Send package to terminals')
        if self.logger.is_debug:
            self.logger.debug('Send package to terminals: {}'.format(
                str(package.repr_debug()),
            ))
        for terminal, output_queue in self.outputs_queues.items():
            self.logger.info('Send package to terminal {}'.format(terminal.__class__.__name__))
            # Terminal maybe don't want all events, so reduce list of event
            # Thirst make a copy to personalize this package
            terminal_adapted_package = copy(package)
            # Duplicate events list to personalize it
            terminal_adapted_package.events = terminal_adapted_package.events[:]

            for package_event in terminal_adapted_package.events[:]:
                if not terminal.accept_event(package_event):
                    terminal_adapted_package.events.remove(package_event)

            if self.logger.is_debug:
                self.logger.debug('Send package to terminal {}: {}'.format(
                    terminal.__class__.__name__,
                    terminal_adapted_package.repr_debug(),
                ))

            output_queue.put(terminal_adapted_package)

    def receive(self) -> [TerminalPackage]:
        self.logger.info('Receive terminals packages')
        packages = []
        for terminal, input_queue in self.inputs_queues.items():
            self.logger.info('Receive terminal {} packages ({})'.format(
                terminal.__class__.__name__,
                'sync' if not terminal.asynchronous else 'async'
            ))
            # When terminal is synchronous, wait it's cycle package
            if not terminal.asynchronous:
                continue_ = True
                while continue_:
                    package = input_queue.get()
                    # In case where terminal send package before end of cycle
                    # management
                    continue_ = not package.is_cycle

                    if self.logger.is_debug:
                        self.logger.debug('Receive package from {}: {}'.format(
                            terminal.__class__.__name__,
                            str(package.repr_debug()),
                        ))

                    packages.append(package)
            else:
                try:
                    while True:
                        package = input_queue.get(block=False, timeout=None)

                        if self.logger.is_debug:
                            self.logger.debug('Receive package from {}: {}'.format(
                                str(terminal),
                                str(package.repr_debug()),
                            ))

                        packages.append(package)
                except Empty:
                    pass  # Queue is empty

        self.logger.info('{} package(s) received'.format(len(packages)))
        return packages
