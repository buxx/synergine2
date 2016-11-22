import cocos
import pyglet
from cocos.actions import Repeat, ScaleBy, Reverse

from sandbox.life_game.simulation import CellDieEvent
from sandbox.life_game.simulation import CellBornEvent
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


class Gui(object):
    def __init__(self, terminal: Terminal):
        self.terminal = terminal
        self.terminal.register_event_handler(CellDieEvent, self.on_cell_die)
        self.terminal.register_event_handler(CellBornEvent, self.on_cell_born)

        cocos.director.director.init()
        self.hello_layer = HelloWorld()
        self.main_scene = cocos.scene.Scene(self.hello_layer)

        self.born = 0
        self.die = 0

        pyglet.clock.schedule_interval(lambda *_, **__: self.terminal.read(), 1 / 60.0)

    def run(self):
        cocos.director.director.run(self.main_scene)

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
