# coding: utf-8
import os

import cocos
from synergine2.config import Config
from synergine2.log import SynergineLogger


class MapMiddleware(object):
    def __init__(
        self,
        config: Config,
        logger: SynergineLogger,
        map_dir_path: str,
    ) -> None:
        self.config = config
        self.logger = logger
        self.map_dir_path = map_dir_path
        self.tmx = None

    def init(self) -> None:
        self.tmx = cocos.tiles.load(os.path.join(
            self.map_dir_path,
            '{}.tmx'.format(os.path.basename(self.map_dir_path)),
        ))

    def get_background_sprite(self) -> cocos.sprite.Sprite:
        raise NotImplementedError()

    def get_ground_layer(self) -> cocos.tiles.RectMapLayer:
        raise NotImplementedError()

    def get_top_layer(self) -> cocos.tiles.RectMapLayer:
        raise NotImplementedError()


class TMXMiddleware(MapMiddleware):
    def get_background_sprite(self) -> cocos.sprite.Sprite:
        return cocos.sprite.Sprite(os.path.join(
            self.map_dir_path,
            'background.png',
        ))

    def get_ground_layer(self) -> cocos.tiles.RectMapLayer:
        assert self.tmx
        return self.tmx['ground']

    def get_top_layer(self) -> cocos.tiles.RectMapLayer:
        assert self.tmx
        return self.tmx['top']
