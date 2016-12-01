from random import randint

import cocos
from cocos.sprite import Sprite
from sandbox.engulf.subject import Cell, Grass
from synergine2.terminals import TerminalPackage
from synergine2_cocos2d.gui import Gui, GridLayerMixin
from synergine2_cocos2d.gui import MainLayer as BaseMainLayer


class CellsLayer(GridLayerMixin, BaseMainLayer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cells = {}

    def born(self, grid_position):
        cell = Sprite('resources/cell.png')
        cell.rotation = randint(0, 360)
        self.grid_manager.scale_sprite(cell)
        self.grid_manager.position_sprite(cell, grid_position)
        self.cells[grid_position] = cell
        self.add(cell)


class GrassLayer(GridLayerMixin, BaseMainLayer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cells = {}

    def born(self, grid_position):
        grass = Sprite('resources/grass.png')
        self.grid_manager.scale_sprite(grass)
        self.grid_manager.position_sprite(grass, grid_position)
        self.cells[grid_position] = grass
        self.add(grass)


class MainLayer(GridLayerMixin, BaseMainLayer):
    def __init__(self, terminal, *args, **kwargs):
        super().__init__(terminal, *args, **kwargs)

        self.cells = CellsLayer(terminal=terminal)
        self.add(self.cells)

        self.grasses = GrassLayer(terminal=terminal)
        self.add(self.grasses)


class Game(Gui):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.main_layer = MainLayer(terminal=self.terminal)
        self.main_scene = cocos.scene.Scene(self.main_layer)
        self.positions = {}

    def get_main_scene(self):
        return self.main_scene

    def before_received(self, package: TerminalPackage):
        if package.subjects:  # It's thirst package
            for subject in package.subjects:
                if isinstance(subject, Cell):
                    self.positions[subject.id] = subject.position
                    self.main_layer.cells.born(subject.position)
                if isinstance(subject, Grass):
                    self.positions[subject.id] = subject.position
                    self.main_layer.grasses.born(subject.position)
