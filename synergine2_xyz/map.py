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
    transform_zero_y_to_bottom = True

    """
    Define default tileset name for layer. key: layer name, value: tileset name
    """
    default_layer_tilesets = {}  # type: typing.Dict[str, str]

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

    def get_default_tile(self, layer_name: str=None) -> XYZTile:
        """
        Return thirst tile of default tileset or thirst tile of given layer default tileset.
        :param layer: if layer given, thirst tile of it's default tileset will be returned
        :return: a Tile
        """
        if layer_name and layer_name in self.default_layer_tilesets:
            tileset_name = self.default_layer_tilesets[layer_name]
            tileset = self.tileset(tileset_name)
        else:
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
            x = -1
            y = 0 if not self.transform_zero_y_to_bottom else self.height - 1
            y_modifier = 1 if not self.transform_zero_y_to_bottom else -1

            self.tmx_layer_tiles[layer_name] = {}

            # no tiles
            if not isinstance(layer, tmx.Layer):
                continue

            for layer_tile in layer.tiles:
                x += 1

                if x == self.width:
                    x = 0
                    y += y_modifier

                position_key = '{}.{}'.format(x, y)

                if not layer_tile.gid:
                    tile = self.get_default_tile(layer_name=layer_name)
                elif not layer_tile.gid in self.tmx_tiles:
                    # tile = UnconstructedTile()
                    tile = self.get_default_tile(layer_name=layer_name)
                else:
                    tile = self.tmx_tiles[layer_tile.gid]

                self.tmx_layer_tiles[layer_name][position_key] = tile

    def layer(self, name: str) -> tmx.Layer:
        return self.tmx_layers[name]

    def tileset(self, name: str) -> tmx.Tileset:
        return self.tmx_tilesets[name]

    def tile(self, gid: int, allow_default_tile: bool=False, default_tile: tmx.LayerTile=None) -> XYZTile:
        try:
            return self.tmx_tiles[gid]
        except KeyError:
            if default_tile:
                return default_tile
            if allow_default_tile:
                return self.get_default_tile()
            raise

    def layer_tiles(self, name: str) -> typing.Dict[str, XYZTile]:
        return self.tmx_layer_tiles[name]
