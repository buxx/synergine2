# coding: utf-8
from synergine2_xyz.map import XYZTile
from synergine2_xyz.physics import MoveCostComputer

if False:
    from sandbox.tile.simulation.base import BaseSubject


class TerrainTile(XYZTile):
    pass


class TileMoveCostComputer(MoveCostComputer):
    def compute_move_cost(
        self,
        subject: 'BaseSubject',
        tile: TerrainTile,
        previous_node: str,
        next_node: str,
        unknown,
    ) -> float:
        # TODO: Objets/IT qui compute les couts de déplacement

        if not tile.property('traversable_by_man'):
            # TODO: revoir la lib disjkstar because les mecs traverses quand meme ...
            return 1000000000000000000000000

        return 1.0
