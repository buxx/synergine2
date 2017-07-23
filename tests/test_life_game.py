# coding: utf-8
import collections

from sandbox.life_game.simulation import Cell
from sandbox.life_game.simulation import Empty
from sandbox.life_game.utils import get_subjects_from_str_representation
from synergine2.config import Config
from synergine2.cycle import CycleManager
from synergine2.log import SynergineLogger
from synergine2_xyz.simulation import XYZSimulation
from synergine2_xyz.subjects import XYZSubjects
from synergine2_xyz.utils import get_str_representation_from_positions
from tests import BaseTest
from tests import str_kwargs


class LifeGameBaseTest(BaseTest):
    def _get_str_representation_of_subjects(self, subjects: list):
        items_positions = collections.defaultdict(list)

        for subject in subjects:
            if type(subject) == Cell:
                items_positions['1'].append(subject.position)
            if type(subject) == Empty:
                items_positions['0'].append(subject.position)

        return get_str_representation_from_positions(
            items_positions,
            complete_lines_with='0',
            **str_kwargs
        )


class TestSimpleSimulation(LifeGameBaseTest):
    def test_cycles_evolution(self):
        simulation = XYZSimulation(Config())
        subjects = self._get_subjects(simulation)
        simulation.subjects = subjects

        cycle_manager = CycleManager(
            Config(),
            SynergineLogger('test'),
            simulation=simulation,
        )

        assert """
            0 0 0 0 0
            0 1 1 1 0
            0 0 0 0 0
        """ == self._get_str_representation_of_subjects(
            subjects,
        )

        cycle_manager.next()

        assert """
            0 0 0 0 0
            0 0 1 0 0
            0 0 1 0 0
            0 0 1 0 0
            0 0 0 0 0
        """ == self._get_str_representation_of_subjects(
            subjects,
        )

        cycle_manager.next()

        assert """
            0 0 0 0 0
            0 0 0 0 0
            0 1 1 1 0
            0 0 0 0 0
            0 0 0 0 0
        """ == self._get_str_representation_of_subjects(
            subjects,
        )

    def _get_subjects(self, simulation: XYZSimulation):
        cells = XYZSubjects(simulation=simulation)

        for position in [
            (-1, 0, 0),
            (0, 0, 0),
            (1, 0, 0),
        ]:
            cells.append(Cell(
                Config(),
                simulation=simulation,
                position=position,
            ))

        for position in [
            (-2, -1, 0),
            (-1, -1, 0),
            (0, -1, 0),
            (1, -1, 0),
            (2, -1, 0),
            (-2, 0, 0),
            (2, 0, 0),
            (-2, 1, 0),
            (-1, 1, 0),
            (0, 1, 0),
            (1, 1, 0),
            (2, 1, 0),
        ]:
            cells.append(Empty(
                Config(),
                simulation=simulation,
                position=position,
            ))
        return cells


class TestMultipleSimulations(LifeGameBaseTest):
    def test_cross(self):
        str_representations = [
            """
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
        """,
            """
            0 0 0 0 0 0 0 0 0 0 0 0
            0 0 0 0 0 1 1 0 0 0 0 0
            0 0 0 0 1 1 1 1 0 0 0 0
            0 0 0 0 0 0 0 0 0 0 0 0
            0 0 1 0 1 0 0 1 0 1 0 0
            0 1 1 0 0 0 0 0 0 1 1 0
            0 1 1 0 0 0 0 0 0 1 1 0
            0 0 1 0 1 0 0 1 0 1 0 0
            0 0 0 0 0 0 0 0 0 0 0 0
            0 0 0 0 1 1 1 1 0 0 0 0
            0 0 0 0 0 1 1 0 0 0 0 0
            0 0 0 0 0 0 0 0 0 0 0 0
        """,
            """
            0 0 0 0 0 0 0 0 0 0 0 0
            0 0 0 0 1 0 0 1 0 0 0 0
            0 0 0 0 1 0 0 1 0 0 0 0
            0 0 0 1 1 0 0 1 1 0 0 0
            0 1 1 1 0 0 0 0 1 1 1 0
            0 0 0 0 0 0 0 0 0 0 0 0
            0 0 0 0 0 0 0 0 0 0 0 0
            0 1 1 1 0 0 0 0 1 1 1 0
            0 0 0 1 1 0 0 1 1 0 0 0
            0 0 0 0 1 0 0 1 0 0 0 0
            0 0 0 0 1 0 0 1 0 0 0 0
            0 0 0 0 0 0 0 0 0 0 0 0
        """,
            """
            0 0 0 0 0 0 0 0 0 0 0 0
            0 0 0 0 0 0 0 0 0 0 0 0
            0 0 0 0 1 1 1 1 0 0 0 0
            0 0 0 0 1 0 0 1 0 0 0 0
            0 0 1 1 1 0 0 1 1 1 0 0
            0 0 1 0 0 0 0 0 0 1 0 0
            0 0 1 0 0 0 0 0 0 1 0 0
            0 0 1 1 1 0 0 1 1 1 0 0
            0 0 0 0 1 0 0 1 0 0 0 0
            0 0 0 0 1 1 1 1 0 0 0 0
            0 0 0 0 0 0 0 0 0 0 0 0
            0 0 0 0 0 0 0 0 0 0 0 0
        """,
        ]

        simulation = XYZSimulation(Config())
        subjects = get_subjects_from_str_representation(
            str_representations[0],
            simulation,
        )
        simulation.subjects = subjects

        cycle_manager = CycleManager(
            config=Config(),
            logger=SynergineLogger('test'),
            simulation=simulation,
        )

        for str_representation in str_representations:
            assert str_representation == \
               self._get_str_representation_of_subjects(
                    subjects,
               )
            cycle_manager.next()
