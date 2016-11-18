import sys
import collections
from sandbox.life_game.simulation import CellBornBehaviour, CellDieBehaviour, Cell, Empty

from sandbox.life_game.utils import get_subjects_from_str_representation
from synergine2.core import Core
from synergine2.cycle import CycleManager
from synergine2.simulation import Simulation
from synergine2.terminals import Terminal
from synergine2.terminals import TerminalPackage
from synergine2.terminals import TerminalManager
from synergine2.xyz_utils import get_str_representation_from_positions


class SimplePrintTerminal(Terminal):
    def __init__(self):
        super().__init__()
        self.subjects = None

    def receive(self, value):
        self.update_with_package(value)
        self.print_str_representation()

    def update_with_package(self, package: TerminalPackage):
        self.subjects = package.subjects if package.subjects else self.subjects
        for subject_id, actions in package.actions.items():
            for action, value in actions.items():
                if action == CellBornBehaviour:
                    # Remove Empty subject
                    self.subjects = [s for s in self.subjects[:] if s.id != subject_id]
                    # Add born subject
                    self.subjects.append(value)
                if action == CellDieBehaviour:
                    # Remove Cell subject
                    self.subjects = [s for s in self.subjects[:] if s.id != subject_id]
                    # Add Empty subject
                    self.subjects.append(value)

    def print_str_representation(self):
        items_positions = collections.defaultdict(list)
        for subject in self.subjects:
            if type(subject) == Cell:
                items_positions['1'].append(subject.position)
            if type(subject) == Empty:
                items_positions['0'].append(subject.position)
        print(get_str_representation_from_positions(
            items_positions,
            separator=' ',
            #force_items_as=(('0', ' '),),
        ))
        print()


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
        cycle_manager=CycleManager(subjects=subjects),
        terminal_manager=TerminalManager([SimplePrintTerminal()]),
    )
    core.run()


if __name__ == '__main__':
    main()
