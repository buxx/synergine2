import cocos
import pyglet
from cocos.actions import Repeat, ScaleBy, Reverse

from sandbox.life_game.simulation import CellDieEvent
from sandbox.life_game.simulation import CellBornEvent
from synergine2.gui import Gui
from synergine2.simulation import Event
from synergine2.terminals import TerminalPackage
from synergine2.terminals import Terminal


class HelloWorld(cocos.layer.Layer):
    def __init__(self):
        super().__init__()

        self.label = cocos.text.Label(
            '...',
            font_name='Times New Roman',
            font_size=21,
            anchor_x='center', anchor_y='center'
        )
        self.label.position = 320, 240
        scale = ScaleBy(3, duration=5)
        self.label.do(Repeat(scale + Reverse(scale)))
        self.add(self.label)


class LifeGameGui(Gui):
    def __init__(
            self,
            terminal: Terminal,
            read_queue_interval: float = 1 / 60.0,
    ):
        super().__init__(terminal, read_queue_interval)

        self.hello_layer = HelloWorld()
        self.main_scene = cocos.scene.Scene(self.hello_layer)

        self.terminal.register_event_handler(CellDieEvent, self.on_cell_die)
        self.terminal.register_event_handler(CellBornEvent, self.on_cell_born)

        self.born = 0
        self.die = 0

    def get_main_scene(self) -> HelloWorld:
        return self.main_scene

    def before_received(self, package: TerminalPackage):
        self.born = 0
        self.die = 0

    def after_received(self, package: TerminalPackage):
        self.hello_layer.label.element.text = 'This cycle: {0} born, {1} dead'.format(
            self.born,
            self.die,
        )

    def on_cell_die(self, event: Event):
        self.die += 1

    def on_cell_born(self, event: Event):
        self.born += 1
