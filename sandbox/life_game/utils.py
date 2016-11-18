from sandbox.life_game.simulation import Empty
from sandbox.life_game.simulation import Cell
from synergine2.simulation import Subjects, Simulation
from synergine2.xyz_utils import get_positions_from_str_representation


def get_subjects_from_str_representation(
    str_representations: str,
    simulation: Simulation,
) -> [Cell, Empty]:
    subjects = Subjects(simulation=simulation)
    items_positions = get_positions_from_str_representation(str_representations)
    for item, positions in items_positions.items():
        for position in positions:
            if item == '0':
                subjects.append(Empty(
                    simulation=simulation,
                    position=position,
                ))
            if item == '1':
                subjects.append(Cell(
                    simulation=simulation,
                    position=position,
                ))
    return subjects