# coding: utf-8
import time

from synergine2.base import BaseObject
from synergine2.config import Config
from synergine2.cycle import CycleManager
from synergine2.log import SynergineLogger
from synergine2.simulation import Simulation
from synergine2.terminals import TerminalManager
from synergine2.terminals import TerminalPackage


class Core(BaseObject):
    def __init__(
        self,
        config: Config,
        logger: SynergineLogger,
        simulation: Simulation,
        cycle_manager: CycleManager,
        terminal_manager: TerminalManager=None,
        cycles_per_seconds: float=1.0,
    ):
        self.config = config
        self.logger = logger
        self.simulation = simulation
        self.cycle_manager = cycle_manager
        self.terminal_manager = terminal_manager or TerminalManager(config, logger, [])
        self._loop_delta = 1./cycles_per_seconds
        self._current_cycle_start_time = None

    def run(self):
        self.logger.info('Run core')
        try:
            self.terminal_manager.start()

            start_package = TerminalPackage(
                subjects=self.simulation.subjects,
            )
            self.logger.info('Send start package to terminals')
            self.terminal_manager.send(start_package)

            while True:
                self._start_cycle()

                events = []
                packages = self.terminal_manager.receive()
                for package in packages:
                    events.extend(self.cycle_manager.apply_actions(
                        simulation_actions=package.simulation_actions,
                        subject_actions=package.subject_actions,
                    ))

                events.extend(self.cycle_manager.next())
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
            pass  # Just stop while
        self.terminal_manager.stop()

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
