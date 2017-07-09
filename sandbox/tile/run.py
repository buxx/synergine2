# coding: utf-8
import argparse
import os
import sys
import logging
from random import seed

from sandbox.tile.simulation.subject import Man

synergine2_path = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../'))
sys.path.append(synergine2_path)

from sandbox.tile.simulation.base import TileStrategySimulation
from sandbox.tile.simulation.base import TileStrategySubjects
from synergine2.log import get_default_logger
from synergine2.config import Config
from sandbox.tile.terminal.base import CocosTerminal
from synergine2.core import Core
from synergine2.cycle import CycleManager
from synergine2.terminals import TerminalManager


def main(map_dir_path: str, seed_value: int=42):
    seed(seed_value)

    config = Config()
    config.load_files(['sandbox/engulf/config.yaml'])
    logger = get_default_logger(level=logging.ERROR)

    simulation = TileStrategySimulation(config)
    subjects = TileStrategySubjects(simulation=simulation)

    man = Man(
        config=config,
        simulation=simulation,
        position=(0, 0),
    )
    man.position = 0, 0
    subjects.append(man)

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
            terminals=[CocosTerminal(
                config,
                logger,
                asynchronous=False,
                map_dir_path=map_dir_path,
            )]
        ),
        cycles_per_seconds=1 / config.core.cycle_duration,
    )
    core.run()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run TileStrategy')
    parser.add_argument('map_dir_path', help='map directory path')
    parser.add_argument('--seed', dest='seed', default=42)

    args = parser.parse_args()

    main(args.map_dir_path, seed_value=args.seed)
