# coding: utf-8
import cocos
import pyglet

from synergine2_cocos2d.gui import Gui
from synergine2_cocos2d.gui import MainLayer
from synergine2_cocos2d.layer import LayerManager
from synergine2_cocos2d.middleware import TMXMiddleware


class Game(Gui):
    def __init__(self, *args, map_dir_path: str, **kwargs):
        super().__init__(*args, **kwargs)
        self.map_dir_path = map_dir_path
        self.layer_manager = LayerManager(
            self.config,
            self.logger,
            middleware=TMXMiddleware(
                self.config,
                self.logger,
                self.map_dir_path,
            ),
        )
        self.layer_manager.init()

        pyglet.clock.schedule_interval(
            lambda *_, **__: self.terminal.read(),
            1 / 60.0,
        )
        cocos.director.director.run(self.layer_manager.main_scene)
