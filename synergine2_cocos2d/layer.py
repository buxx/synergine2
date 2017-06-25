# coding: utf-8
import typing

import cocos
from synergine2.config import Config
from synergine2.log import SynergineLogger
from synergine2_cocos2d.gui import MainLayer
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
        self.background_layers = []  # type: typing.List[cocos.layer.Layer]
        self.subject_layers = []  # type: typing.List[cocos.layer.Layer]
        self.decoration_layers = []  # type: typing.List[cocos.layer.Layer]

    @property
    def background(self) -> cocos.layer.Layer:
        return self.background_layers[0]

    @property
    def subject(self) -> cocos.layer.Layer:
        return self.background_layers[0]

    @property
    def decoration(self) -> cocos.layer.Layer:
        return self.background_layers[0]

    def init(self) -> None:
        self.main_layer = MainLayer()  # self.terminal) TODO: Ne plus donner le terminal

        self.background_layers.extend(self.middleware.get_background_layers())
        self.subject_layers.append(cocos.layer.Layer())
        self.decoration_layers.extend(self.middleware.get_decoration_layers())

        for layer in self.background_layers:
            self.main_layer.add(layer)

        for layer in self.subject_layers:
            self.main_layer.add(layer)

        for layer in self.decoration_layers:
            self.main_layer.add(layer)
