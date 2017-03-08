# coding: utf-8
from random import randint

import cocos
from cocos.actions import MoveTo, Repeat, ScaleBy, Reverse, RotateTo
from cocos.sprite import Sprite
from sandbox.engulf.behaviour import GrassGrownUp, GrassSpawn, MoveTo as MoveToEvent, EatEvent, AttackEvent
from sandbox.engulf.subject import Cell, Grass, PreyCell, PredatorCell
from synergine2.terminals import TerminalPackage
from synergine2_cocos2d.gui import Gui, GridLayerMixin
from synergine2_cocos2d.gui import MainLayer as BaseMainLayer

cell_scale = ScaleBy(1.1, duration=0.25)


class CellsLayer(GridLayerMixin, BaseMainLayer):
    def __init__(self, game: 'Game', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.game = game
        self.cell_positions = {}
        self.cell_ids = {}

    @property
    def move_duration(self):
        return self.game.cycle_duration

    @property
    def fake_move_rotate_duration(self):
        return self.move_duration / 3

    def born(self, subject_id: int, grid_position, cell_type):
        png = 'resources/cell.png' if cell_type is PreyCell else 'resources/cellp.png'

        cell = Sprite(png)
        cell.rotation = randint(0, 360)
        self.grid_manager.scale_sprite(cell)
        self.grid_manager.position_sprite(cell, grid_position)
        self.cell_positions[grid_position] = cell
        self.cell_ids[subject_id] = cell
        cell.do(Repeat(cell_scale + Reverse(cell_scale)))
        self.add(cell)

    def move(self, subject_id: int, position: tuple):
        cell = self.cell_ids[subject_id]

        window_position = self.grid_manager.get_window_position(position[0], position[1])
        move_action = MoveTo(window_position, self.move_duration)

        fake_rotate = RotateTo(randint(0, 360), self.fake_move_rotate_duration)

        cell.do(move_action)
        cell.do(fake_rotate)

    def attack(self, attacker_id: int, attacked_id: int):
        attacker = self.cell_ids[attacker_id]
        attacker.do(ScaleBy(1.7, duration=0.25))


class GrassLayer(GridLayerMixin, BaseMainLayer):
    def __init__(self, game: 'Game', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.game = game
        self.grasses = {}

    def born(self, subject_id, grid_position, opacity=100):
        grass = Sprite('resources/grass.png')
        grass.rotation = randint(0, 360)
        grass.opacity = opacity
        self.grid_manager.scale_sprite(grass)
        self.grid_manager.position_sprite(grass, grid_position)
        self.grasses[subject_id] = grass
        self.add(grass)

    def set_density(self, subject_id, density):
        self.grasses[subject_id].opacity = density


class MainLayer(GridLayerMixin, BaseMainLayer):
    def __init__(self, game: 'Game', terminal, *args, **kwargs):
        super().__init__(terminal, *args, **kwargs)
        self.game = game

        self.cells = CellsLayer(game=game, terminal=terminal)
        self.add(self.cells)

        self.grasses = GrassLayer(game=game, terminal=terminal)
        self.add(self.grasses)


class Game(Gui):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.main_layer = MainLayer(game=self, terminal=self.terminal)
        self.main_scene = cocos.scene.Scene(self.main_layer)

        # Event registering
        self.terminal.register_event_handler(
            GrassGrownUp,
            self.on_grass_grown_up,
        )
        self.terminal.register_event_handler(
            GrassSpawn,
            self.on_grass_spawn,
        )
        self.terminal.register_event_handler(
            MoveToEvent,
            self.on_move_to,
        )
        self.terminal.register_event_handler(
            EatEvent,
            self.on_eat,
        )
        self.terminal.register_event_handler(
            AttackEvent,
            self.on_attack,
        )

    def get_main_scene(self):
        return self.main_scene

    def before_received(self, package: TerminalPackage):
        if package.subjects:  # It's thirst package
            for subject in package.subjects:
                if isinstance(subject, PreyCell):
                    self.main_layer.cells.born(subject.id, subject.position, PreyCell)
                if isinstance(subject, PredatorCell):
                    self.main_layer.cells.born(subject.id, subject.position, PredatorCell)
                if isinstance(subject, Grass):
                    self.main_layer.grasses.born(
                        subject.id,
                        subject.position,
                        subject.density,
                    )

    def on_grass_spawn(self, event: GrassSpawn):
        self.main_layer.grasses.born(
            event.subject_id,
            event.position,
            event.density,
        )

    def on_grass_grown_up(self, event: GrassGrownUp):
        self.main_layer.grasses.set_density(
            event.subject_id,
            event.density,  # TODO: Recupe ces données depuis local plutôt que event ?
        )

    def on_move_to(self, event: MoveToEvent):
        self.main_layer.cells.move(
            event.subject_id,
            event.position,
        )

    def on_eat(self, event: EatEvent):
        self.main_layer.grasses.set_density(
            event.eaten_id,
            event.eaten_new_density,
        )

    def on_attack(self, event: AttackEvent):
        self.main_layer.cells.attack(
            event.attacker_id,
            event.attacked_id,
        )
