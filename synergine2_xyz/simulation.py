# coding: utf-8
import typing

from dijkstar import Graph

from synergine2.config import Config
from synergine2.simulation import Simulation as BaseSimulation
from synergine2_xyz.subjects import XYZSubjects
from synergine2_xyz.subjects import XYZSubject


class XYZSimulation(BaseSimulation):
    accepted_subject_class = XYZSubjects

    def __init__(
        self,
        config: Config,
    ) -> None:
        super().__init__(config)
        self.graph = Graph()

        # TODO: Le graph devra être calculé à partir de données comme tmx
        for y in range(40):
            for x in range(70):
                position = '{}.{}'.format(x, y)
                neighbors = []

                for modifier_x, modifier_y in (
                    (+1, +1),
                    (+1, +0),
                    (+1, -1),
                    (+0, -1),
                    (-1, -1),
                    (-1, +0),
                    (-1, -1),
                    (+0, +1),
                ):
                    try:
                        neighbors.append('{}.{}'.format(x+modifier_x, y+modifier_y))
                    except ValueError:
                        pass

                for neighbor in neighbors:
                    neighbor_x, neighbor_y = map(int, neighbor.split('.'))

                    if neighbor_x > 69 or neighbor_x < 0:
                        continue

                    if neighbor_y > 69 or neighbor_y < 0:
                        continue

                    # TODO: Voir https://pypi.python.org/pypi/Dijkstar/2.2
                    self.graph.add_edge(position, neighbor, 1)
        pass

    def is_possible_subject_position(self, subject: XYZSubject, position: tuple) -> bool:
        return self.is_possible_position(position)

    def is_possible_position(self, position: tuple) -> bool:
        return True
