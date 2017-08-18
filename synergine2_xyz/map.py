# coding: utf-8
import typing

import tmx

from synergine2_xyz.exceptions import ImproperlyConfiguredMap


class XYZTile(object):
    def __init__(self, tile: tmx.Tile) -> None:
        self.tile = tile

    def property(self, name: str) -> typing.Union[str, int, float]:
        for property in self.tile.properties:
            if property.name == name:
                return property.value

        raise ImproperlyConfiguredMap('Tile with id "{}" don\'t contains "{}" property'.format(
            self.tile.id,
            name,
        ))


class UnconstructedTile(XYZTile):
    pass


class TMXMap(object):
    xyz_tile_class = XYZTile

    def __init__(self, map_file_path: str) -> None:
        self.tmx_map = tmx.TileMap.load(map_file_path)
        self.tmx_layers = {}  # type: typing.Dict[str, tmx.Layer]
        self.tmx_layer_tiles = {}  # type: typing.Dict[str, typing.Dict[str, XYZTile]]
        self.tmx_tilesets = {}  # type: typing.Dict[str, tmx.Tileset]
        self.tmx_tiles = {}  # type: typing.Dict[int, XYZTile]
        self._load()

    @property
    def height(self) -> int:
        return self.tmx_map.height

    @property
    def width(self) -> int:
        return self.tmx_map.width

    def get_default_tileset(self) -> tmx.Tileset:
        return list(self.tmx_tilesets.values())[0]

    def get_default_tile(self) -> XYZTile:
        tileset = self.get_default_tileset()
        return self.xyz_tile_class(tileset.tiles[0])

    def _load(self) -> None:
        self._load_layers()
        self._load_tilesets()
        self._load_tiles()

    def _load_layers(self) -> None:
        for layer in self.tmx_map.layers:
            self.tmx_layers[layer.name] = layer

    def _load_tilesets(self) -> None:
        for tileset in self.tmx_map.tilesets:
            self.tmx_tilesets[tileset.name] = tileset
            for tile in tileset.tiles:
                self.tmx_tiles[tileset.firstgid + tile.id] = self.xyz_tile_class(tile)

    def _load_tiles(self) -> None:
        for layer_name, layer in self.tmx_layers.items():
            x, y = -1, 0
            self.tmx_layer_tiles[layer_name] = {}

            # no tiles
            if not isinstance(layer, tmx.Layer):
                continue

            for layer_tile in layer.tiles:
                x += 1

                if x == self.width:
                    x = 0
                    y += 1

                position_key = '{}.{}'.format(x, y)

                if not layer_tile.gid:
                    tile = self.get_default_tile()
                elif not layer_tile.gid in self.tmx_tiles:
                    # tile = UnconstructedTile()
                    tile = self.get_default_tile()
                else:
                    tile = self.tmx_tiles[layer_tile.gid]

                self.tmx_layer_tiles[layer_name][position_key] = tile

    def layer(self, name: str) -> tmx.Layer:
        return self.tmx_layers[name]

    def tileset(self, name: str) -> tmx.Tileset:
        return self.tmx_tilesets[name]

    def tile(self, gid: int) -> XYZTile:
        return self.tmx_tiles[gid]

    def layer_tiles(self, name: str) -> typing.Dict[str, XYZTile]:
        return self.tmx_layer_tiles[name]
