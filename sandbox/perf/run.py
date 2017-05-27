from random import seed
import logging
import os
import sys

synergine2_ath = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../'))
sys.path.append(synergine2_ath)


from sandbox.perf.simulation import ComputeSubject
from synergine2.config import Config
from synergine2.core import Core
from synergine2.cycle import CycleManager
from synergine2.log import get_default_logger
from synergine2.simulation import Simulation, Subjects
from synergine2.terminals import TerminalManager


def main():
    seed(42)

    config = Config(dict(complexity=10000))
    logger = get_default_logger(level=logging.ERROR)

    simulation = Simulation(config)
    subjects = Subjects(simulation=simulation)
    subjects.extend([ComputeSubject(
        config=config,
        simulation=simulation,
    ) for i in range(500)])
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
            terminals=[]
        ),
        cycles_per_seconds=1000000,
    )
    core.run()


if __name__ == '__main__':
    main()
