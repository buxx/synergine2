# coding: utf-8
import typing

import tmx
from dijkstar import Graph
from dijkstar import find_path

from synergine2.config import Config
from synergine2_xyz.map import TMXMap
from synergine2_xyz.tmx_utils import get_layer_by_name


class Physics(object):
    def __init__(
        self,
        config: Config,
    ) -> None:
        self.config = config
        self.graph = Graph()

    def load(self) -> None:
        raise NotImplementedError()

    def position_to_key(self, position: typing.Tuple[int, int]) -> str:
        return '{}.{}'.format(*position)

    def found_path(
        self,
        start: typing.Tuple[int, int],
        end: typing.Tuple[int, int],
    ) -> typing.List[typing.Tuple[int, int]]:
        start_key = self.position_to_key(start)
        end_key = self.position_to_key(end)

        found_path = find_path(self.graph, start_key, end_key)
        regular_path = []
        for position in found_path[0][1:]:
            x, y = map(int, position.split('.'))
            regular_path.append((x, y))

        return regular_path


class TMXPhysics(Physics):
    def __init__(
        self,
        config: Config,
        map_file_path: str,
    ) -> None:
        super().__init__(config)
        self.map_file_path = map_file_path

    def load(self) -> None:
        self.load_graph_from_map(self.map_file_path)

    def load_graph_from_map(self, map_file_path: str) -> None:
        tmx_map = TMXMap(map_file_path)

        # TODO: tmx_map contient tout en cache, faire le dessous en exploitant tmx_map.
        for y in range(tmx_map.height):
            for x in range(tmx_map.width):
                position = self.position_to_key((x, y))
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
                        neighbors.append('{}.{}'.format(x + modifier_x, y + modifier_y))
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
