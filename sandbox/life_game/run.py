# coding: utf-8
import os
import sys

import logging

from synergine2.config import Config
from synergine2.log import get_default_logger

synergine2_ath = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../'))
sys.path.append(synergine2_ath)

import collections

from sandbox.life_game.simulation import Cell, LotOfCellsSignalBehaviour, LifeGame, \
    EmptyPositionWithLotOfCellAroundEvent
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
            # force_positions_as=(
            #     ((-3, -10, 0), 'V'),
            #     ((-2, -9, 0), 'X'),
            # )
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
        EmptyPositionWithLotOfCellAroundEvent,
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
        0 0 0 0 0 0 0 0 0 0 0 0 0
        0 0 0 1 1 1 1 0 0 0 0 0 0
        0 0 0 1 0 0 1 0 0 0 0 0 0
        0 1 1 1 0 0 1 1 1 0 0 0 0
        0 1 0 0 0 0 0 0 1 0 0 0 0
        0 1 0 0 0 0 0 0 1 0 0 0 0
        0 1 1 1 0 0 1 1 1 0 0 0 0
        0 0 0 1 0 0 1 0 0 0 0 0 0
        0 0 0 1 1 1 1 0 0 0 0 0 0
        0 0 0 0 0 0 0 0 0 0 0 0 0
        0 0 0 0 0 0 0 0 0 0 0 0 0
        0 0 0 0 0 0 0 0 0 0 0 0 0
        0 0 0 0 0 0 0 0 0 0 0 0 0
        0 0 0 0 0 0 0 0 0 0 0 0 0
        0 0 0 0 0 1 1 1 0 0 0 0 0
        0 0 0 0 0 0 0 1 0 0 0 0 0
        0 0 0 0 0 0 1 0 0 0 0 0 0
        0 0 0 0 0 0 0 0 0 0 0 0 0
        0 0 0 0 0 0 0 0 0 0 0 0 0
    """
    simulation = LifeGame()
    subjects = get_subjects_from_str_representation(
        start_str_representation,
        simulation,
    )
    simulation.subjects = subjects

    config = Config()
    logger = get_default_logger(level=logging.DEBUG)

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
            terminals=[CocosTerminal(), SimplePrintTerminal()]
        ),
    )
    core.run()


if __name__ == '__main__':
    main()
