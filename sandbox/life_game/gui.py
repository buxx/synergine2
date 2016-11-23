import cocos
from cocos.actions import ScaleBy, Repeat, Reverse, RotateBy
from cocos.director import director
from cocos.layer import ScrollableLayer, Layer
from cocos.sprite import Sprite
from pyglet.window import key as wkey
from random import randint

from sandbox.life_game.simulation import CellDieEvent, Cell
from sandbox.life_game.simulation import CellBornEvent
from synergine2.gui import Gui
from synergine2.terminals import TerminalPackage
from synergine2.terminals import Terminal

cell_scale = ScaleBy(1.1, duration=0.25)
cell_rotate = RotateBy(360, duration=30)


class GridManager(object):
    def __init__(self, square_width: int, border: int=0):
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


class Cells(Layer):
    def __init__(self):
        super().__init__()
        self.cells = {}
        self.grid_manager = GridManager(32, border=2)

    def born(self, grid_position):
        cell = Sprite('resources/cells_l.png')
        cell.rotation = randint(0, 360)
        self.grid_manager.scale_sprite(cell)
        self.grid_manager.position_sprite(cell, grid_position)
        cell.do(Repeat(cell_scale + Reverse(cell_scale)))
        cell.do(Repeat(cell_rotate + Reverse(cell_rotate)))
        self.cells[grid_position] = cell
        self.add(cell)

    def die(self, grid_position):
        self.remove(self.cells[grid_position])
        del self.cells[grid_position]


class MainLayer(ScrollableLayer):
    is_event_handler = True

    def __init__(self):
        super().__init__()

        self.scroll_step = 20

        self.background = Sprite('resources/banner-1711735_640.jpg')
        self.background.position = 0, 0
        self.background.opacity = 70
        self.background.scale = 5
        self.add(self.background, z=1)

        self.cells = Cells()
        self.add(self.cells)

        self.cross = Sprite('resources/cross31x31.png')
        self.cross.position = 0, 0
        self.cross.opacity = 50
        self.add(self.cross)

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


class LifeGameGui(Gui):
    def __init__(
            self,
            terminal: Terminal,
            read_queue_interval: float = 1 / 60.0,
    ):
        super().__init__(terminal, read_queue_interval)

        self.main_layer = MainLayer()
        self.main_scene = cocos.scene.Scene(self.main_layer)
        self.positions = {}

        self.terminal.register_event_handler(CellDieEvent, self.on_cell_die)
        self.terminal.register_event_handler(CellBornEvent, self.on_cell_born)

    def get_main_scene(self):
        return self.main_scene

    def before_received(self, package: TerminalPackage):
        if package.subjects:  # It's thirst package
            for subject in package.subjects:
                if isinstance(subject, Cell):
                    self.positions[subject.id] = subject.position
                    self.main_layer.cells.born(subject.position)

    def on_cell_die(self, event: CellDieEvent):
        self.main_layer.cells.die(self.positions[event.subject_id])

    def on_cell_born(self, event: CellBornEvent):
        # TODO: La position peut evoluer dans un autre programme
        # resoudre cette problematique de données subjects qui évolue
        subject = self.terminal.subjects.get(event.subject_id)
        self.positions[event.subject_id] = subject.position
        self.main_layer.cells.born(subject.position)
