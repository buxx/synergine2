# coding: utf-8
import typing

import cocos

from synergine2.config import Config
from synergine2.log import SynergineLogger
from synergine2_cocos2d.middleware import MapMiddleware


class LayerManager(object):
    def __init__(
        self,
        config: Config,
        logger: SynergineLogger,
        middleware: MapMiddleware,
    ) -> None:
        self.config = config
        self.logger = logger
        self.middleware = middleware

        self.main_scene = None  # type: cocos.scene.Scene
        self.main_layer = None  # type: cocos.layer.Layer

        self.background_sprite = None  # type: cocos.sprite.Sprite
        self.ground_layer = None  # type: cocos.tiles.RectMapLayer
        self.subject_layer = None  # type: cocos.tiles.RectMapLayer
        self.top_layer = None  # type: cocos.tiles.RectMapLayer

    def init(self) -> None:
        from synergine2_cocos2d.gui import MainLayer

        self.middleware.init()
        self.main_layer = MainLayer()
        self.main_scene = cocos.scene.Scene(self.main_layer)

        self.background_sprite = self.middleware.get_background_sprite()
        self.ground_layer = self.middleware.get_ground_layer()
        self.subject_layer = self.get_subjects_layer()
        self.top_layer = self.middleware.get_top_layer()

        self.main_layer.add(self.background_sprite)
        self.main_layer.add(self.ground_layer)
        self.main_layer.add(self.subject_layer)
        self.main_layer.add(self.top_layer)

    def get_subjects_layer(self) -> cocos.tiles.RectMapLayer:
        # TODO: hardcoded values: use TMX infos
        cells = self.generate_subjects_cells(width=70, height=40, tile_width=8, tile_height=8)
        return cocos.tiles.RectMapLayer(
            id='subject',
            tw=8,  # hardcoded values: use TMX infos
            th=8,  # hardcoded values: use TMX infos
            cells=cells,
        )

    def generate_subjects_cells(
        self,
        width: int,
        height: int,
        tile_width: int,
        tile_height: int,
    ) -> typing.List[typing.List[cocos.tiles.RectCell]]:
        cells = [[None] * height for x in range(width)]  # type: typing.List[typing.List[cocos.tiles.RectCell]]
        for n in range(width * height):
            i = n % width
            j = height - (n // width + 1)
            # TODO: C'est ici que l'on met une tile=XXX avec des subjects
            cells[i][j] = cocos.tiles.RectCell(i, j, tile_width, tile_height, properties={}, tile=None)
        return cells

    def center(self):
        self.background_sprite.set_position(
            0 + (self.background_sprite.width / 2),
            0 + (self.background_sprite.height / 2),
        )
        self.ground_layer.set_view(0, 0, self.ground_layer.px_width, self.ground_layer.px_height)
        self.subject_layer.position = 0, 0
        self.top_layer.set_view(0, 0, self.top_layer.px_width, self.top_layer.px_height)

        self.main_scene.position = - self.ground_layer.px_width / 2, - self.ground_layer.px_height / 2
