# coding: utf-8
import cocos
from cocos.actions import ScaleBy, Repeat, Reverse, RotateBy
from cocos.director import director
from cocos.layer import ScrollableLayer, Layer
from cocos.sprite import Sprite
from pyglet.window import key as wkey
from random import randint
from sandbox.life_game.simulation import CellBornEvent
from sandbox.life_game.simulation import CellDieEvent, Cell, InvertCellStateBehaviour, \
    EmptyPositionWithLotOfCellAroundEvent
from synergine2.config import Config
from synergine2.log import SynergineLogger
from synergine2.terminals import Terminal
from synergine2.terminals import TerminalPackage
from synergine2_cocos2d.gui import Gui, GridLayerMixin, MainLayer as BaseMainLayer

cell_scale = ScaleBy(1.1, duration=0.25)
cell_rotate = RotateBy(360, duration=30)
flash_flash = ScaleBy(8, duration=0.5)
flash_rotate = RotateBy(360, duration=6)


class Cells(GridLayerMixin, Layer):
    def __init__(self):
        super().__init__()
        self.cells = {}
        self.flashs = []

    def born(self, grid_position):
        if grid_position in self.cells:
            return  # cell can be added by gui

        cell = Sprite('resources/cells_l.png')
        cell.rotation = randint(0, 360)
        self.grid_manager.scale_sprite(cell)
        self.grid_manager.position_sprite(cell, grid_position)
        cell.do(Repeat(cell_scale + Reverse(cell_scale)))
        cell.do(Repeat(cell_rotate + Reverse(cell_rotate)))
        self.cells[grid_position] = cell
        self.add(cell)

    def die(self, grid_position):
        try:
            self.remove(self.cells[grid_position])
            del self.cells[grid_position]
        except KeyError:
            pass  # Cell can be removed by gui

    def flash(self, position):
        flash = Sprite('resources/flash.png')
        flash.opacity = 40
        flash.scale = 0.1
        flash.rotation = randint(0, 360)
        flash.do(flash_flash + Reverse(flash_flash))
        flash.do(Repeat(flash_rotate + Reverse(flash_rotate)))
        self.grid_manager.position_sprite(flash, position)
        self.flashs.append(flash)
        self.add(flash)


class MainLayer(GridLayerMixin, BaseMainLayer):
    is_event_handler = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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

    def on_mouse_press(self, x, y, buttons, modifiers):
        x, y = director.get_virtual_coordinates(x, y)
        grid_position = self.grid_manager.get_grid_position(x, y)

        self.terminal.send(TerminalPackage(
            simulation_actions=[(InvertCellStateBehaviour, {'position': grid_position})],
        ))

    def on_mouse_motion(self, x, y, dx, dy):
        x, y = director.get_virtual_coordinates(x, y)
        grid_position = self.grid_manager.get_grid_position(x, y)
        window_position = self.grid_manager.get_window_position(grid_position[0], grid_position[1])

        self.cross.position = window_position


class LifeGameGui(Gui):
    def __init__(
            self,
            config: Config,
            logger: SynergineLogger,
            terminal: Terminal,
            read_queue_interval: float=1 / 60.0,
    ):
        super().__init__(config, logger, terminal, read_queue_interval)

        self.main_layer = MainLayer(terminal=self.terminal)
        self.main_scene = cocos.scene.Scene(self.main_layer)
        self.positions = {}

        self.terminal.register_event_handler(CellDieEvent, self.on_cell_die)
        self.terminal.register_event_handler(CellBornEvent, self.on_cell_born)
        self.terminal.register_event_handler(
            EmptyPositionWithLotOfCellAroundEvent,
            self.on_empty_cell_with_lot_of_cell_around,
        )

    def get_main_scene(self):
        return self.main_scene

    def before_received(self, package: TerminalPackage):
        if package.subjects:  # It's thirst package
            for subject in package.subjects:
                if isinstance(subject, Cell):
                    self.positions[subject.id] = subject.position
                    self.main_layer.cells.born(subject.position)

        for flash in self.main_layer.cells.flashs[:]:
            self.main_layer.cells.flashs.remove(flash)
            self.main_layer.cells.remove(flash)

    def on_cell_die(self, event: CellDieEvent):
        try:
            self.main_layer.cells.die(self.positions[event.subject_id])
        except KeyError:
            pass

    def on_cell_born(self, event: CellBornEvent):
        if event.subject_id not in self.terminal.subjects:
            return

        subject = self.terminal.subjects.get(event.subject_id)
        self.positions[event.subject_id] = subject.position
        self.main_layer.cells.born(subject.position)

    def on_empty_cell_with_lot_of_cell_around(self, event: EmptyPositionWithLotOfCellAroundEvent):
        self.main_layer.cells.flash(event.position)
