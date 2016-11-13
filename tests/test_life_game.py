import collections
from sandbox.life_game.simulation import Cell, Empty
from synergine2.cycle import CycleManager
from synergine2.simulation import Simulation, Subjects
from synergine2.utils import initialize_subject
from synergine2.xyz_utils import get_str_representation_from_positions
from tests import BaseTest, str_kwargs


class TestSimpleSimulation(BaseTest):
    def test_cycles_evolution(self):
        simulation = Simulation()
        subjects = self._get_subjects(simulation)
        simulation.subjects = subjects

        cycle_manager = CycleManager(
            subjects=subjects,
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
            0 0 1 0 0
            0 0 1 0 0
            0 0 1 0 0
        """ == self._get_str_representation_of_subjects(
            subjects,
        )

        cycle_manager.next()

        assert """
            0 0 0 0 0
            0 1 1 1 0
            0 0 0 0 0
        """ == self._get_str_representation_of_subjects(
            subjects,
        )

    def _get_subjects(self, simulation: Simulation):
        cells = Subjects(simulation=simulation)

        for position in [
            (-1, 0, 0),
            (0, 0, 0),
            (1, 0, 0),
        ]:
            cells.append(Cell(
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
                simulation=simulation,
                position=position,
            ))
        return cells

    def _get_str_representation_of_subjects(self, subjects: list):
        items_positions = collections.defaultdict(list)

        for subject in subjects:
            if type(subject) == Cell:
                items_positions['1'].append(subject.position)
            if type(subject) == Empty:
                items_positions['0'].append(subject.position)

        return get_str_representation_from_positions(
            items_positions,
            **str_kwargs
        )
