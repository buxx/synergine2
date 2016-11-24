import collections

from sandbox.life_game.simulation import Cell
from sandbox.life_game.simulation import Empty
from sandbox.life_game.simulation import CellDieEvent
from sandbox.life_game.simulation import CellBornEvent
from sandbox.life_game.utils import get_subjects_from_str_representation
from synergine2.core import Core
from synergine2.cycle import CycleManager
from synergine2.simulation import Simulation
from synergine2.simulation import Event
from synergine2.terminals import Terminal
from synergine2.terminals import TerminalPackage
from synergine2.terminals import TerminalManager
from synergine2.xyz_utils import get_str_representation_from_positions


class SimplePrintTerminal(Terminal):
    subscribed_events = [
        CellDieEvent,
        CellBornEvent,
    ]

    def __init__(self):
        super().__init__()
        self._cycle_born_count = 0
        self._cycle_die_count = 0
        self.register_event_handler(CellDieEvent, self.record_die)
        self.register_event_handler(CellBornEvent, self.record_born)

    def record_die(self, event: Event):
        self._cycle_die_count += 1

    def record_born(self, event: Event):
        self._cycle_born_count += 1

    def receive(self, package: TerminalPackage):
        self._cycle_born_count = 0
        self._cycle_die_count = 0
        super().receive(package)
        self.print_str_representation()

    def print_str_representation(self):
        items_positions = collections.defaultdict(list)
        for subject in self.subjects.values():
            if type(subject) == Cell:
                items_positions['1'].append(subject.position)
            if type(subject) == Empty:
                items_positions['0'].append(subject.position)
        print(get_str_representation_from_positions(
            items_positions,
            separator=' ',
            force_items_as=(('0', ' '),),
        ))

        # Display current cycle events
        print('This cycle: {0} born, {1} dead'.format(
            self._cycle_born_count,
            self._cycle_die_count,
        ))

        print()


class CocosTerminal(Terminal):
    subscribed_events = [
        CellDieEvent,
        CellBornEvent,
    ]

    def __init__(self):
        super().__init__()
        self.subjects = None
        self.gui = None

    def receive(self, package: TerminalPackage):
        self.gui.before_received(package)
        super().receive(package)
        self.gui.after_received(package)

    def run(self):
        from sandbox.life_game import gui
        self.gui = gui.LifeGameGui(self)
        self.gui.run()


def main():
    start_str_representation = """
        0 0 0 0 0 0 0 0 0 0 0
        0 0 0 1 1 1 1 0 0 0 0
        0 0 0 1 0 0 1 0 0 0 0
        0 1 1 1 0 0 1 1 1 0 0
        0 1 0 0 0 0 0 0 1 0 0
        0 1 0 0 0 0 0 0 1 0 0
        0 1 1 1 0 0 1 1 1 0 0
        0 0 0 1 0 0 1 0 0 0 0
        0 0 0 1 1 1 1 0 0 0 0
        0 0 0 0 0 0 0 0 0 0 0
        0 0 0 0 0 0 0 0 0 0 0
    """
    simulation = Simulation()
    subjects = get_subjects_from_str_representation(
        start_str_representation,
        simulation,
    )
    simulation.subjects = subjects

    core = Core(
        simulation=simulation,
        cycle_manager=CycleManager(simulation=simulation),
        terminal_manager=TerminalManager([CocosTerminal(), SimplePrintTerminal()]),
    )
    core.run()


if __name__ == '__main__':
    main()
