from synergine2.cycle import CycleManager
from synergine2.simulation import Simulation
from synergine2.terminals import TerminalManager
from synergine2.terminals import TerminalPackage


class Core(object):
    def __init__(
        self,
        simulation: Simulation,
        cycle_manager: CycleManager,
        terminal_manager: TerminalManager=None,

    ):
        self.simulation = simulation
        self.cycle_manager = cycle_manager
        self.terminal_manager = terminal_manager or TerminalManager([])

    def run(self):
        try:
            self.terminal_manager.start()

            start_package = TerminalPackage(
                subjects=self.simulation.subjects,
            )
            self.terminal_manager.send(start_package)

            while True:
                events = []
                packages = self.terminal_manager.receive()
                for package in packages:
                    events.extend(self.cycle_manager.apply_actions(package.actions))

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

                import time
                time.sleep(1)  # TODO: tick control
        except KeyboardInterrupt:
            pass  # Just stop while
        self.terminal_manager.stop()
