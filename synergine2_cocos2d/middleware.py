# coding: utf-8
import os

import cocos
from synergine2.config import Config
from synergine2.log import get_logger


class MapMiddleware(object):
    def __init__(
        self,
        config: Config,
        map_dir_path: str,
    ) -> None:
        self.config = config
        self.logger = get_logger(self.__class__.__name__, config)
        self.map_dir_path = map_dir_path
        self.tmx = None

    def get_map_file_path(self) -> str:
        return os.path.join(
            self.map_dir_path,
            '{}.tmx'.format(os.path.basename(self.map_dir_path)),
        )

    def init(self) -> None:
        map_file_path = self.get_map_file_path()
        self.tmx = cocos.tiles.load(map_file_path)

    def get_background_sprite(self) -> cocos.sprite.Sprite:
        raise NotImplementedError()

    def get_ground_layer(self) -> cocos.tiles.RectMapLayer:
        raise NotImplementedError()

    def get_top_layer(self) -> cocos.tiles.RectMapLayer:
        raise NotImplementedError()

    def get_world_height(self) -> int:
        raise NotImplementedError()

    def get_world_width(self) -> int:
        raise NotImplementedError()

    def get_cell_height(self) -> int:
        raise NotImplementedError()

    def get_cell_width(self) -> int:
        raise NotImplementedError()


class TMXMiddleware(MapMiddleware):
    def get_background_sprite(self) -> cocos.sprite.Sprite:
        # TODO: Extract it from tmx
        return cocos.sprite.Sprite(os.path.join(
            self.map_dir_path,
            'background.png',
        ))

    def get_interior_sprite(self) -> cocos.sprite.Sprite:
        # TODO: Extract it from tmx
        return cocos.sprite.Sprite(os.path.join(
            self.map_dir_path,
            'background_interiors.png',
        ))

    def get_ground_layer(self) -> cocos.tiles.RectMapLayer:
        assert self.tmx
        return self.tmx['ground']

    def get_top_layer(self) -> cocos.tiles.RectMapLayer:
        assert self.tmx
        return self.tmx['top']

    def get_world_height(self) -> int:
        return len(self.tmx['ground'].cells[0])

    def get_world_width(self) -> int:
        return len(self.tmx['ground'].cells)

    def get_cell_height(self) -> int:
        return self.tmx['ground'].cells[0][0].size[1]

    def get_cell_width(self) -> int:
        return self.tmx['ground'].cells[0][0].size[0]
