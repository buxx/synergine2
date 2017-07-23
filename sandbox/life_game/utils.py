# coding: utf-8
from sandbox.life_game.simulation import Cell
from sandbox.life_game.simulation import Empty
from synergine2.simulation import Simulation
from synergine2_xyz.subjects import XYZSubjects
from synergine2_xyz.utils import get_positions_from_str_representation


def get_subjects_from_str_representation(
    str_representations: str,
    simulation: Simulation,
) -> [Cell, Empty]:
    subjects = XYZSubjects(simulation=simulation)
    items_positions = get_positions_from_str_representation(str_representations)
    for item, positions in items_positions.items():
        for position in positions:
            if item == '0':
                subjects.append(Empty(
                    config=simulation.config,
                    simulation=simulation,
                    position=position,
                ))
            if item == '1':
                subjects.append(Cell(
                    config=simulation.config,
                    simulation=simulation,
                    position=position,
                ))
    return subjects