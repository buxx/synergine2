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
import logging
import os
import sys
import typing

synergine2_ath = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../'))
sys.path.append(synergine2_ath)

from random import randint, seed
from sandbox.engulf.behaviour import GrassGrownUp, GrassSpawn, MoveTo, EatEvent, AttackEvent, EatenEvent

from synergine2.config import Config
from synergine2.log import get_default_logger
from sandbox.engulf.subject import Cell, Grass, PreyCell, PredatorCell
from synergine2.core import Core
from synergine2.cycle import CycleManager
from synergine2.terminals import TerminalManager, Terminal, TerminalPackage
from sandbox.engulf.simulation import EngulfSubjects, Engulf
from synergine2.xyz_utils import get_around_positions_of, get_distance_between_points


class GameTerminal(Terminal):
    subscribed_events = [
        GrassGrownUp,
        GrassSpawn,
        MoveTo,
        EatEvent,
        AttackEvent,
        EatenEvent,
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.gui = None
        self.asynchronous = False  # TODO: config

    def receive(self, package: TerminalPackage):
        self.gui.before_received(package)
        super().receive(package)
        self.gui.after_received(package)

    def run(self):
        from sandbox.engulf import gui
        self.gui = gui.Game(self.config, self.logger, self)
        self.gui.run()


def fill_with_random_cells(
    config,
    subjects: EngulfSubjects,
    count: int,
    start_position: tuple,
    end_position: tuple,
    cell_class: typing.Type[PreyCell],
) -> None:
    cells = []

    while len(cells) < count:
        position = (
            randint(start_position[0], end_position[0]+1),
            randint(start_position[1], end_position[1]+1),
            0,
        )
        if position not in subjects.cell_xyz:
            cell = cell_class(
                config,
                simulation=subjects.simulation,
                position=position,
            )
            cells.append(cell)
            subjects.append(cell)


def fill_with_random_grass(
    config,
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
            0,
        )

        if position not in subjects.grass_xyz:
            grass = Grass(
                config,
                simulation=subjects.simulation,
                position=position,
            )
            grasses.append(grass)
            subjects.append(grass)

    for grass in grasses:
        for around in get_around_positions_of(grass.position, distance=density):
            if around not in subjects.grass_xyz:
                if subjects.simulation.is_possible_position(around):
                    new_grass = Grass(
                        config,
                        simulation=subjects.simulation,
                        position=around,
                    )
                    distance = get_distance_between_points(around, grass.position)
                    new_grass.density = 100 - round((distance * 100) / 7)
                    subjects.append(new_grass)


def main():
    seed(42)

    config = Config()
    config.load_files(['sandbox/engulf/config.yaml'])
    logger = get_default_logger(level=logging.DEBUG)

    simulation = Engulf(config)
    subjects = EngulfSubjects(simulation=simulation)
    fill_with_random_cells(
        config,
        subjects,
        30,
        (-34, -34, 0),
        (34, 34, 0),
        cell_class=PreyCell,
    )
    fill_with_random_cells(
        config,
        subjects,
        30,
        (-34, -34, 0),
        (34, 34, 0),
        cell_class=PredatorCell,
    )
    fill_with_random_grass(
        config,
        subjects,
        5,
        (-34, -34, 0),
        (34, 34, 0),
    )
    simulation.subjects = subjects

    core = Core(
        config=config,
        logger=logger,
        simulation=simulation,
        cycle_manager=CycleManager(
            config=config,
            logger=logger,
            simulation=simulation,
        ),
        terminal_manager=TerminalManager(
            config=config,
            logger=logger,
            terminals=[GameTerminal(
                config,
                logger,
                asynchronous=False,
            )]
        ),
        cycles_per_seconds=1/config.core.cycle_duration,
    )
    core.run()


if __name__ == '__main__':
    main()