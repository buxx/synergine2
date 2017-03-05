# coding: utf-8
import cocos
import pyglet
from pyglet.window import key as wkey
from cocos.director import director
from cocos.layer import ScrollableLayer, Layer
from cocos.sprite import Sprite

from synergine2.config import Config
from synergine2.log import SynergineLogger
from synergine2.terminals import Terminal
from synergine2.terminals import TerminalPackage


class GridManager(object):
    def __init__(
        self,
        layer: Layer,
        square_width: int,
        border: int=0,
    ):
        self.layer = layer
        self.square_width = square_width
        self.border = border

    @property
    def final_width(self):
        return self.square_width + self.border

    def scale_sprite(self, sprite: Sprite):
        sprite.scale_x = self.final_width / sprite.image.width
        sprite.scale_y = self.final_width / sprite.image.height

    def position_sprite(self, sprite: Sprite, grid_position):
        grid_x = grid_position[0]
        grid_y = grid_position[1]
        sprite.position = grid_x * self.final_width, grid_y * self.final_width

    def get_window_position(self, grid_position_x, grid_position_y):
        grid_x = grid_position_x
        grid_y = grid_position_y
        return grid_x * self.final_width, grid_y * self.final_width

    def get_grid_position(self, window_x, window_y, z=0) -> tuple:
        window_size = director.get_window_size()

        window_center_x = window_size[0] // 2
        window_center_y = window_size[1] // 2

        window_relative_x = window_x - window_center_x
        window_relative_y = window_y - window_center_y

        real_width = self.final_width * self.layer.scale

        return int(window_relative_x // real_width),\
               int(window_relative_y // real_width),\
               z


class GridLayerMixin(object):
    def __init__(self, *args, **kwargs):
        square_width = kwargs.pop('square_width', 32)
        square_border = kwargs.pop('square_border', 2)
        self.grid_manager = GridManager(
            self,
            square_width=square_width,
            border=square_border,
        )
        super().__init__(*args, **kwargs)


class MainLayer(ScrollableLayer):
    is_event_handler = True

    def __init__(self, terminal: Terminal, scroll_step: int=100):
        super().__init__()

        self.terminal = terminal
        self.scroll_step = scroll_step
        self.grid_manager = GridManager(self, 32, border=2)

        # Set scene center on center of screen
        window_size = director.get_window_size()
        self.position = window_size[0] // 2, window_size[1] // 2

    def on_key_press(self, key, modifiers):
        if key == wkey.LEFT:
            self.position = (self.position[0] + self.scroll_step, self.position[1])

        if key == wkey.RIGHT:
            self.position = (self.position[0] - self.scroll_step, self.position[1])

        if key == wkey.UP:
            self.position = (self.position[0], self.position[1] - self.scroll_step)

        if key == wkey.DOWN:
            self.position = (self.position[0], self.position[1] + self.scroll_step)

        if key == wkey.A:
            if self.scale >= 0.3:
                self.scale -= 0.2

        if key == wkey.Z:
            if self.scale <= 4:
                self.scale += 0.2


class Gui(object):
    def __init__(
            self,
            config: Config,
            logger: SynergineLogger,
            terminal: Terminal,
            read_queue_interval: float= 1/60.0,
    ):
        self.config = config
        self.logger = logger,
        self._read_queue_interval = read_queue_interval
        self.terminal = terminal
        self.cycle_duration = self.config.core.cycle_duration
        cocos.director.director.init()

    def run(self):
        pyglet.clock.schedule_interval(
            lambda *_, **__: self.terminal.read(),
            self._read_queue_interval,
        )
        cocos.director.director.run(self.get_main_scene())

    def get_main_scene(self) -> cocos.cocosnode.CocosNode:
        raise NotImplementedError()

    def before_received(self, package: TerminalPackage):
        pass

    def after_received(self, package: TerminalPackage):
        pass
