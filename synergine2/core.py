# coding: utf-8
import time

from multiprocessing import Queue

from synergine2.base import BaseObject
from synergine2.config import Config
from synergine2.cycle import CycleManager
from synergine2.log import get_logger
from synergine2.simulation import Simulation
from synergine2.terminals import TerminalManager
from synergine2.terminals import Terminal
from synergine2.terminals import TerminalPackage
from synergine2.utils import time_it


class Core(BaseObject):
    def __init__(
        self,
        config: Config,
        simulation: Simulation,
        cycle_manager: CycleManager,
        terminal_manager: TerminalManager=None,
        cycles_per_seconds: float=1.0,
    ):
        self.config = config
        self.logger = get_logger('Core', config)
        self.simulation = simulation
        self.cycle_manager = cycle_manager
        self.terminal_manager = terminal_manager or TerminalManager(config, [])
        self._loop_delta = 1./cycles_per_seconds
        self._current_cycle_start_time = None
        self._continue = True
        self.main_process_terminal = None  # type: Terminal

    def run(
        self,
        from_terminal: Terminal=None,
        from_terminal_input_queue: Queue=None,
        from_terminal_output_queue: Queue=None,
    ):
        self.logger.info('Run core')
        try:
            # Execute terminal in main process if needed
            if not from_terminal:
                self.main_process_terminal \
                    = self.terminal_manager.get_main_process_terminal()
                if self.main_process_terminal:
                    self.logger.info(
                        'The "{}" terminal have to be the main process'
                        ', start it now'.format(
                            self.main_process_terminal.__class__.__name__,
                        ),
                    )
                    self.main_process_terminal.execute_as_main_process(self)
                    return
            else:
                # A terminal is main process, so we have to add it's queues to terminal
                # manager
                self.terminal_manager.inputs_queues[from_terminal] \
                    = from_terminal_input_queue
                self.terminal_manager.outputs_queues[from_terminal] \
                    = from_terminal_output_queue

            self.terminal_manager.start()

            start_package = TerminalPackage(
                subjects=self.simulation.subjects,
            )
            self.logger.info('Send start package to terminals')
            self.terminal_manager.send(start_package)

            while self._continue:
                self._start_cycle()

                events = []
                packages = self.terminal_manager.receive()
                for package in packages:
                    if package.sigterm:
                        self.logger.info('SIGTERM received from terminal package')
                        self._continue = False

                    events.extend(self.cycle_manager.apply_actions(
                        simulation_actions=package.simulation_actions,
                        subject_actions=package.subject_actions,
                    ))

                with time_it() as elapsed_time:
                    events.extend(self.cycle_manager.next())

                self.logger.info('Cycle duration: {}s'.format(
                    elapsed_time.get_final_time(),
                ))

                cycle_package = TerminalPackage(
                    events=events,
                    add_subjects=self.simulation.subjects.adds,
                    remove_subjects=self.simulation.subjects.removes,
                    is_cycle=True,
                )
                self.terminal_manager.send(cycle_package)

                # Reinitialize these list for next cycle
                self.simulation.subjects.adds = []
                self.simulation.subjects.removes = []

                self._end_cycle()
        except KeyboardInterrupt:
            self.logger.info('KeyboardInterrupt: stop the loop')
            pass  # Just stop while
        except Exception as exc:
            self.logger.exception('Fatal error during simulation')

        self.logger.info('Getting out of loop. Terminating.')
        self.terminal_manager.stop()
        self.cycle_manager.stop()
        self.logger.info('Terminated')

    def _start_cycle(self):
        time_ = time.time()
        self.logger.info('Start cycle at time {}'.format(time_))
        self._current_cycle_start_time = time_

    def _end_cycle(self) -> None:
        """
        Make a sleep if cycle duration take less time of wanted (see
        cycles_per_seconds constructor parameter)
        """
        time_ = time.time()
        self.logger.info('End of cycle at time {}'.format(time_))
        cycle_duration = time_ - self._current_cycle_start_time
        sleep_time = self._loop_delta - cycle_duration
        self.logger.info('Sleep time is {}'.format(sleep_time))
        if sleep_time > 0:
            time.sleep(sleep_time)
