"""

Engulf is simulation containing:

* Subjects who need to:
  * eat
    * low energy ground stuff
    * other alive subjects
    * other dead subjects
  * sleep
  * want to be not alone
    * with non aggressive subjects
  * want to be alone
  * reproduce
    * with non aggressive subjects
    * and transmit tendencies because their cultures can be
      * eat: - eat background stuff, + eat subjects
      * alone/not alone: - be alone + not alone

"""
from random import randint

from sandbox.engulf.subject import Cell
from synergine2.core import Core
from synergine2.cycle import CycleManager
from synergine2.terminals import TerminalManager, Terminal, TerminalPackage
from synergine2.xyz import Simulation
from synergine2.xyz import XYZSubjects


class Engulf(Simulation):
    pass


class GameTerminal(Terminal):
    subscribed_events = []

    def __init__(self):
        super().__init__()
        self.gui = None

    def receive(self, package: TerminalPackage):
        self.gui.before_received(package)
        super().receive(package)
        self.gui.after_received(package)

    def run(self):
        from sandbox.engulf import gui
        self.gui = gui.Game(self)
        self.gui.run()


def get_random_subjects(
        simulation: Simulation,
        count: int,
        x_min: int,
        y_min: int,
        x_max: int,
        y_max: int,
) -> [Cell]:
    cells = XYZSubjects(simulation=simulation)

    while len(cells) < count:
        position = (
            randint(x_min, x_max+1),
            randint(y_min, y_max+1),
            0
        )
        if position not in cells.xyz:
            cells.append(Cell(
                simulation=simulation,
                position=position,
            ))

    return cells


def main():
    simulation = Engulf()
    subjects = get_random_subjects(
        simulation,
        30,
        -34,
        -34,
        34,
        34,
    )
    simulation.subjects = subjects

    core = Core(
        simulation=simulation,
        cycle_manager=CycleManager(simulation=simulation),
        terminal_manager=TerminalManager([GameTerminal()]),
    )
    core.run()


if __name__ == '__main__':
    main()
