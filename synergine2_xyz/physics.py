# coding: utf-8
import typing

from dijkstar import Graph
from dijkstar import find_path

from synergine2.config import Config
from synergine2_xyz.map import TMXMap, XYZTile
from synergine2_xyz.subjects import XYZSubject
from synergine2_xyz.xyz import get_neighbor_positions


class MoveCostComputer(object):
    def __init__(
        self,
        config: Config,
    ) -> None:
        self.config = config

    def for_subject(self, subject: XYZSubject):
        # TODO: Verifier ce que sont les parametres pour les nommer correctement
        def move_cost_func(previous_node: str, next_node: str, tile: XYZTile, unknown):
            return self.compute_move_cost(subject, tile, previous_node, next_node, unknown)
        return move_cost_func

    def compute_move_cost(
        self,
        subject: XYZSubject,
        tile: XYZTile,
        previous_node: str,
        next_node: str,
        unknown,
    ) -> float:
        return 1.0


class Physics(object):
    move_cost_computer_class = MoveCostComputer

    def __init__(
        self,
        config: Config,
    ) -> None:
        self.config = config
        self.graph = Graph()
        self.move_cost_computer = self.move_cost_computer_class(config)

    def load(self) -> None:
        raise NotImplementedError()

    def position_to_key(self, position: typing.Tuple[int, int]) -> str:
        return '{}.{}'.format(*position)

    def found_path(
        self,
        start: typing.Tuple[int, int],
        end: typing.Tuple[int, int],
        subject: XYZSubject,
    ) -> typing.List[typing.Tuple[int, int]]:
        start_key = self.position_to_key(start)
        end_key = self.position_to_key(end)

        found_path = find_path(self.graph, start_key, end_key, cost_func=self.move_cost_computer.for_subject(subject))
        regular_path = []
        for position in found_path[0][1:]:
            x, y = map(int, position.split('.'))
            regular_path.append((x, y))

        return regular_path


class TMXPhysics(Physics):
    tmx_map_class = TMXMap

    def __init__(
        self,
        config: Config,
        map_file_path: str,
    ) -> None:
        super().__init__(config)
        self.map_file_path = map_file_path
        self.tmx_map = self.tmx_map_class(map_file_path)

    def load(self) -> None:
        self.load_graph_from_map(self.map_file_path)

    def load_graph_from_map(self, map_file_path: str) -> None:
        # TODO: tmx_map contient tout en cache, faire le dessous en exploitant tmx_map.
        for y in range(self.tmx_map.height):
            for x in range(self.tmx_map.width):
                position = self.position_to_key((x, y))

                for neighbor_position in get_neighbor_positions((x, y)):
                    neighbor = '{}.{}'.format(*neighbor_position)
                    neighbor_x, neighbor_y = neighbor_position

                    if neighbor_x > self.tmx_map.width-1 or neighbor_x < 0:
                        continue

                    if neighbor_y > self.tmx_map.height-1 or neighbor_y < 0:
                        continue

                    # Note: movement consider future tile properties
                    to_tile = self.tmx_map.layer_tiles('terrain')[neighbor]
                    # Note: Voir https://pypi.python.org/pypi/Dijkstar/2.2
                    self.graph.add_edge(position, neighbor, to_tile)
