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
from random import randint, seed
from sandbox.engulf.behaviour import GrassGrownUp, GrassSpawn, GrassSpawnBehaviour

from sandbox.engulf.subject import Cell, Grass, COLLECTION_GRASS
from synergine2.core import Core
from synergine2.cycle import CycleManager
from synergine2.terminals import TerminalManager, Terminal, TerminalPackage
from synergine2.xyz import Simulation
from sandbox.engulf.simulation import EngulfSubjects
from synergine2.xyz_utils import get_around_positions_of, get_distance_between_points


class Engulf(Simulation):
    behaviours_classes = [
        GrassSpawnBehaviour,
    ]


class GameTerminal(Terminal):
    subscribed_events = [
        GrassGrownUp,
        GrassSpawn,
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.gui = None

    def receive(self, package: TerminalPackage):
        self.gui.before_received(package)
        super().receive(package)
        self.gui.after_received(package)

    def run(self):
        from sandbox.engulf import gui
        self.gui = gui.Game(self)
        self.gui.run()


def fill_with_random_cells(
    subjects: EngulfSubjects,
    count: int,
    start_position: tuple,
    end_position: tuple,
) -> None:
    cells = []

    while len(cells) < count:
        position = (
            randint(start_position[0], end_position[0]+1),
            randint(start_position[1], end_position[1]+1),
            randint(start_position[2], end_position[2]+1),
        )
        if position not in subjects.cell_xyz:
            cell = Cell(
                simulation=subjects.simulation,
                position=position,
            )
            cells.append(cell)
            subjects.append(cell)


def fill_with_random_grass(
    subjects: EngulfSubjects,
    start_count: int,
    start_position: tuple,
    end_position: tuple,
    density: int=5,
) -> None:
    grasses = []

    while len(grasses) < start_count:
        position = (
            randint(start_position[0], end_position[0]+1),
            randint(start_position[1], end_position[1]+1),
            randint(start_position[2], end_position[2]+1),
        )

        if position not in subjects.grass_xyz:
            grass = Grass(
                simulation=subjects.simulation,
                position=position,
            )
            grasses.append(grass)
            subjects.append(grass)

    for grass in grasses:
        for around in get_around_positions_of(grass.position, distance=density):
            if around not in subjects.grass_xyz:
                new_grass = Grass(
                    simulation=subjects.simulation,
                    position=around,
                )
                distance = get_distance_between_points(around, grass.position)
                new_grass.density = 100 - round((distance * 100) / 7)
                subjects.append(new_grass)


def main():
    seed(0)
    simulation = Engulf()
    subjects = EngulfSubjects(simulation=simulation)
    fill_with_random_cells(
        subjects,
        30,
        (-34, -34, 0),
        (34, 34, 0),
    )
    fill_with_random_grass(
        subjects,
        5,
        (-34, -34, 0),
        (34, 34, 0),
    )
    simulation.subjects = subjects

    core = Core(
        simulation=simulation,
        cycle_manager=CycleManager(simulation=simulation),
        terminal_manager=TerminalManager([GameTerminal(
            asynchronous=False,
        )]),
        cycles_per_seconds=1,
    )
    core.run()


if __name__ == '__main__':
    main()
