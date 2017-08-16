# coding: utf-8
import typing

import tmx


class UnconstructedTile(object):
    pass


class TMXMap(object):
    def __init__(self, map_file_path: str) -> None:
        self.tmx_map = tmx.TileMap.load(map_file_path)
        self.tmx_layers = {}  # type: typing.Dict[str, tmx.Layer]
        self.tmx_layer_tiles = {}  # type: typing.Dict[str, typing.Dict[str, tmx.Tile]]
        self.tmx_tilesets = {}  # type: typing.Dict[str, tmx.Tileset]
        self.tmx_tiles = {}  # type: typing.Dict[int, tmx.Tile]
        self._load()

    @property
    def height(self) -> int:
        return self.tmx_map.height

    @property
    def width(self) -> int:
        return self.tmx_map.width

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
                self.tmx_tiles[tileset.firstgid + tile.id] = tile

    def _load_tiles(self) -> None:
        for layer_name, layer in self.tmx_layers.items():
            x, y = -1, -1
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
                    tile = None
                elif not layer_tile.gid in self.tmx_tiles:
                    tile = UnconstructedTile()
                else:
                    tile = self.tmx_tiles[layer_tile.gid]

                self.tmx_layer_tiles[layer_name][position_key] = tile

    def layer(self, name: str) -> tmx.Layer:
        return self.tmx_layers[name]

    def tileset(self, name: str) -> tmx.Tileset:
        return self.tmx_tilesets[name]

    def tile(self, gid: int) -> tmx.Tile:
        return self.tmx_tiles[gid]
