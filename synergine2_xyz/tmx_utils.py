# coding: utf-8
import typing

from tmx import TileMap
from tmx import Layer

from synergine2.exceptions import ConfigurationError
from synergine2_xyz.map import TMXMap

if typing.TYPE_CHECKING:
    from synergine2_xyz.physics import Matrixes


def get_layer_by_name(map_: TileMap, layer_name: str) -> Layer:
    for layer in map_.layers:
        if layer.name == layer_name:
            return layer

    raise ConfigurationError('No layer named "{}" in map')


def fill_matrix(
    tmx_map: TMXMap,
    matrixes: 'Matrixes',
    layer_name: str,
    matrix_name: str,
    properties: typing.List[str],
) -> None:
    for tile_xy, tile in tmx_map.tmx_layer_tiles[layer_name].items():
        x, y = map(int, tile_xy.split('.'))
        values = [tile.property(p_name) for p_name in properties]
        matrixes.update_matrix(matrix_name, value=tuple(values), x=x, y=y)
