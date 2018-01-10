# coding: utf-8
import typing

from pyglet.window import key

import cocos

from synergine2.config import Config
from synergine2.log import SynergineLogger, get_logger
from synergine2_cocos2d.middleware import MapMiddleware

if False:
    from synergine2_cocos2d.actor import Actor
    from synergine2_cocos2d.gui import GridManager
    from synergine2_cocos2d.gui import Gui
    from synergine2_cocos2d.interaction import InteractionManager


class ScrollingManager(cocos.layer.ScrollingManager):
    def world_to_screen_positions(
        self,
        positions: typing.List[typing.Tuple[int, int]],
    ) -> typing.List[typing.Tuple[int, int]]:
        screen_positions = []

        for position in positions:
            scx, scy = self.world_to_screen(
                position[0],
                position[1],
            )
            screen_positions.append((scx, scy))

        return screen_positions

    def screen_to_world_positions(
        self,
        positions: typing.List[typing.Tuple[int, int]],
    ) -> typing.List[typing.Tuple[int, int]]:
        world_positions = []

        for position in positions:
            wx, wy = self.screen_to_world(
                position[0],
                position[1],
            )
            world_positions.append((wx, wy))

        return world_positions


class SubjectLayer(cocos.layer.ScrollableLayer):
    def __init__(self, parallax: int=1):
        super().__init__(parallax)
        self.subjects_index = {}  # type: typing.Dict[int, Actor]

    def add_subject(self, actor: 'Actor') -> None:
        self.add(actor)
        self.subjects_index[actor.subject.id] = actor


class LayerManager(object):
    edit_layer_class = None  # type: typing.Type['EditLayer']

    def __init__(
        self,
        config: Config,
        middleware: MapMiddleware,
        interaction_manager: 'InteractionManager',
        gui: 'Gui',
    ) -> None:
        self.config = config
        self.logger = get_logger('LayerManager', config)
        self.middleware = middleware
        self.interaction_manager = interaction_manager
        self.gui = gui

        self.grid_manager = None  # type: GridManager
        self.scrolling_manager = None  # type: ScrollingManager
        self.main_scene = None  # type: cocos.scene.Scene
        self.main_layer = None  # type: cocos.layer.Layer
        self.edit_layer = None  # TODO type

        self.background_sprite = None  # type: cocos.sprite.Sprite
        self.ground_layer = None  # type: cocos.tiles.RectMapLayer
        self.subject_layer = None  # type: SubjectLayer
        self.top_layer = None  # type: cocos.tiles.RectMapLayer

        from synergine2_cocos2d.gui import EditLayer
        self.edit_layer_class = self.edit_layer_class or EditLayer
        self.debug = self.config.resolve('global.debug', False)

    def init(self) -> None:
        # TODO: cyclic import
        from synergine2_cocos2d.gui import MainLayer
        from synergine2_cocos2d.gui import GridManager

        self.middleware.init()

        self.grid_manager = GridManager(
            self.middleware.get_cell_width(),
            self.middleware.get_cell_height(),
            self.middleware.get_world_width(),
            self.middleware.get_world_height(),
        )

        self.main_scene = cocos.scene.Scene()
        self.scrolling_manager = ScrollingManager()

        self.main_layer = MainLayer(
            self,
            self.grid_manager,
            **{
                'width': 1200,  # Note: world size
                'height': 1000,  # Note: world size
            }
        )
        self.edit_layer = self.edit_layer_class(
            self.config,
            self,
            self.grid_manager,
            self.main_layer,
            **{
                'bindings': {
                    key.LEFT: 'left',
                    key.RIGHT: 'right',
                    key.UP: 'up',
                    key.DOWN: 'down',
                    key.NUM_ADD: 'zoomin',
                    key.NUM_SUBTRACT: 'zoomout'
                },
                'mod_modify_selection': key.MOD_SHIFT,
                'mod_restricted_mov': key.MOD_ACCEL,
                'fastness': 160.0,
                'autoscroll_border': 20.0,  # in pixels, float; None disables autoscroll
                'autoscroll_fastness': 320.0,
                'wheel_multiplier': 2.5,
                'zoom_min': 0.1,
                'zoom_max': 2.0,
                'zoom_fastness': 1.0
            }
        )

        self.main_scene.add(self.scrolling_manager)
        self.scrolling_manager.add(self.main_layer, z=0)
        self.main_scene.add(self.edit_layer)

        self.interior_sprite = self.middleware.get_interior_sprite()
        self.background_sprite = self.middleware.get_background_sprite()
        self.ground_layer = self.middleware.get_ground_layer()
        self.subject_layer = SubjectLayer()
        self.top_layer = self.middleware.get_top_layer()

        self.main_layer.add(self.interior_sprite)
        self.main_layer.add(self.background_sprite)
        self.main_layer.add(self.ground_layer)
        self.main_layer.add(self.subject_layer)
        self.main_layer.add(self.top_layer)

    def center(self):
        self.interior_sprite.position = 0 + (self.interior_sprite.width/2), 0 + (self.interior_sprite.height/2)
        self.background_sprite.position = 0 + (self.background_sprite.width/2), 0 + (self.background_sprite.height/2)
        self.ground_layer.set_view(0, 0, self.ground_layer.px_width, self.ground_layer.px_height)
        self.subject_layer.position = 0, 0
        self.top_layer.set_view(0, 0, self.top_layer.px_width, self.top_layer.px_height)

    def add_subject(self, subject: 'Actor') -> None:
        self.subject_layer.add_subject(subject)

    def remove_subject(self, subject: 'Actor') -> None:
        self.subject_layer.remove(subject)

    def set_selectable(self, subject: 'Actor') -> None:
        self.edit_layer.set_selectable(subject)

    def unset_selectable(self, subject: 'Actor') -> None:
        self.edit_layer.unset_selectable(subject)
