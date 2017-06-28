# coding: utf-8
import argparse
import os
import sys
import logging
from random import seed

synergine2_path = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../'))
sys.path.append(synergine2_path)

from sandbox.tiledstrategy.simulation.base import TiledStrategySimulation, TiledStrategySubjects
from synergine2.log import get_default_logger
from synergine2.config import Config
from sandbox.tiledstrategy.terminal.base import CocosTerminal
from synergine2.core import Core
from synergine2.cycle import CycleManager
from synergine2.terminals import TerminalManager


def main(map_dir_path: str, seed_value: int=42):
    seed(seed_value)

    config = Config()
    config.load_files(['sandbox/engulf/config.yaml'])
    logger = get_default_logger(level=logging.ERROR)

    simulation = TiledStrategySimulation(config)
    subjects = TiledStrategySubjects(simulation=simulation)
    # TODO: Create subjects
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
    parser = argparse.ArgumentParser(description='Run TiledStrategy')
    parser.add_argument('map_dir_path', help='map directory path')
    parser.add_argument('--seed', dest='seed', default=42)

    args = parser.parse_args()

    main(args.map_dir_path, seed_value=args.seed)
