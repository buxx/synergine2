# coding: utf-8
import tmx

from sandbox.tile.simulation.physics import TerrainTile
from sandbox.tile.simulation.physics import TileMoveCostComputer
from synergine2.config import Config
from synergine2_xyz.map import TMXMap
from synergine2_xyz.physics import Physics
from synergine2_xyz.physics import TMXPhysics
from synergine2_xyz.simulation import XYZSimulation
from synergine2_xyz.subjects import XYZSubjects
from synergine2_xyz.subjects import XYZSubject


class TileMap(TMXMap):
    xyz_tile_class = TerrainTile

    def get_default_tileset(self) -> tmx.Tileset:
        return self.tmx_tilesets['terrain']


class TilePhysics(TMXPhysics):
    tmx_map_class = TileMap
    move_cost_computer_class = TileMoveCostComputer


class TileStrategySimulation(XYZSimulation):
    behaviours_classes = [

    ]

    def __init__(
        self,
        config: Config,
        map_file_path: str,
    ) -> None:
        self.map_file_path = map_file_path
        super().__init__(config)

    def create_physics(self) -> Physics:
        return TilePhysics(
            config=self.config,
            map_file_path=self.map_file_path,
        )


class TileStrategySubjects(XYZSubjects):
    pass


class BaseSubject(XYZSubject):
    pass
