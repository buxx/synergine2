# coding: utf-8
from tmx import TileMap
from tmx import Layer

from synergine2.exceptions import ConfigurationError


def get_layer_by_name(map_: TileMap, layer_name: str) -> Layer:
    for layer in map_.layers:
        if layer.name == layer_name:
            return layer

    raise ConfigurationError('No layer named "{}" in map')
