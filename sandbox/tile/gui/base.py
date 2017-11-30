# coding: utf-8
import os
import random
import typing

import pyglet
from pyglet.window import key

from cocos.actions import MoveTo as BaseMoveTo
from cocos.audio.pygame.mixer import Sound
from sandbox.tile.user_action import UserAction
from synergine2.config import Config
from synergine2.log import SynergineLogger
from synergine2.terminals import Terminal
from synergine2_cocos2d.actions import MoveTo
from synergine2_cocos2d.animation import ANIMATION_CRAWL
from synergine2_cocos2d.animation import ANIMATION_WALK
from synergine2_cocos2d.animation import Animate
from synergine2_cocos2d.gl import draw_line
from synergine2_cocos2d.gui import EditLayer as BaseEditLayer
from synergine2_cocos2d.gui import TMXGui
from synergine2_cocos2d.layer import LayerManager
from synergine2_xyz.move.simulation import FinishMoveEvent
from synergine2_xyz.move.simulation import StartMoveEvent
from synergine2_xyz.physics import Physics
from synergine2_xyz.utils import get_angle
from sandbox.tile.simulation.event import NewVisibleOpponent
from sandbox.tile.simulation.event import NoLongerVisibleOpponent
from sandbox.tile.simulation.event import FireEvent
from sandbox.tile.simulation.event import DieEvent


class EditLayer(BaseEditLayer):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def _on_key_press(self, k, m):
        if self.selection:
            if k == key.M:
                self.user_action_pending = UserAction.ORDER_MOVE
            if k == key.R:
                self.user_action_pending = UserAction.ORDER_MOVE_FAST
            if k == key.C:
                self.user_action_pending = UserAction.ORDER_MOVE_CRAWL
            if k == key.F:
                self.user_action_pending = UserAction.ORDER_FIRE


class TileLayerManager(LayerManager):
    edit_layer_class = EditLayer


# TODO: Move into synergine2cocos2d
class AudioLibrary(object):
    sound_file_paths = {
        'gunshot_default': '204010__duckduckpony__homemade-gunshot-2.ogg',
    }

    def __init__(self, sound_dir_path: str) -> None:
        self._sound_dir_path = sound_dir_path
        self._sounds = {}

    def get_sound(self, name: str) -> Sound:
        if name not in self._sounds:
            sound_file_name = self.sound_file_paths[name]
            self._sounds[name] = Sound(os.path.join(self._sound_dir_path, sound_file_name))
        return self._sounds[name]


class Game(TMXGui):
    layer_manager_class = TileLayerManager

    def __init__(
        self,
        config: Config,
        logger: SynergineLogger,
        terminal: Terminal,
        physics: Physics,
        read_queue_interval: float = 1 / 60.0,
        map_dir_path: str=None,
    ):
        super().__init__(
            config,
            logger,
            terminal,
            physics=physics,
            read_queue_interval=read_queue_interval,
            map_dir_path=map_dir_path,
        )
        self.sound_lib = AudioLibrary('sandbox/tile/sounds/')

        self.terminal.register_event_handler(
            FinishMoveEvent,
            self.set_subject_position,
        )

        self.terminal.register_event_handler(
            StartMoveEvent,
            self.start_move_subject,
        )

        self.terminal.register_event_handler(
            NewVisibleOpponent,
            self.new_visible_opponent,
        )

        self.terminal.register_event_handler(
            NoLongerVisibleOpponent,
            self.no_longer_visible_opponent,
        )

        self.terminal.register_event_handler(
            FireEvent,
            self.fire_happen,
        )

        self.terminal.register_event_handler(
            DieEvent,
            self.subject_die,
        )

        # configs
        self.move_duration_ref = float(self.config.resolve('game.move.walk_ref_time'))
        self.move_fast_duration_ref = float(self.config.resolve('game.move.run_ref_time'))
        self.move_crawl_duration_ref = float(self.config.resolve('game.move.crawl_ref_time'))

    def before_run(self) -> None:
        from sandbox.tile.gui.move import MoveActorInteraction
        from sandbox.tile.gui.move import MoveFastActorInteraction
        from sandbox.tile.gui.move import MoveCrawlActorInteraction
        from sandbox.tile.gui.fire import FireActorInteraction

        self.layer_manager.interaction_manager.register(MoveActorInteraction, self.layer_manager)
        self.layer_manager.interaction_manager.register(MoveFastActorInteraction, self.layer_manager)
        self.layer_manager.interaction_manager.register(MoveCrawlActorInteraction, self.layer_manager)
        self.layer_manager.interaction_manager.register(FireActorInteraction, self.layer_manager)

    def set_subject_position(self, event: FinishMoveEvent):
        actor = self.layer_manager.subject_layer.subjects_index[event.subject_id]
        new_world_position = self.layer_manager.grid_manager.get_world_position_of_grid_position(event.to_position)

        actor.stop_actions((BaseMoveTo,))
        actor.set_position(*new_world_position)

    def start_move_subject(self, event: StartMoveEvent):
        actor = self.layer_manager.subject_layer.subjects_index[event.subject_id]
        new_world_position = self.layer_manager.grid_manager.get_world_position_of_grid_position(event.to_position)

        if event.gui_action == UserAction.ORDER_MOVE:
            animation = ANIMATION_WALK
            cycle_duration = 2
            move_duration = self.move_duration_ref
        elif event.gui_action == UserAction.ORDER_MOVE_FAST:
            animation = ANIMATION_WALK
            cycle_duration = 0.5
            move_duration = self.move_fast_duration_ref
        elif event.gui_action == UserAction.ORDER_MOVE_CRAWL:
            animation = ANIMATION_CRAWL
            cycle_duration = 2
            move_duration = self.move_crawl_duration_ref
        else:
            raise NotImplementedError()

        move_action = MoveTo(new_world_position, move_duration)
        actor.do(move_action)
        actor.do(Animate(animation, duration=move_duration, cycle_duration=cycle_duration))
        actor.rotation = get_angle(event.from_position, event.to_position)

    def new_visible_opponent(self, event: NewVisibleOpponent):
        self.visible_or_no_longer_visible_opponent(event, (153, 0, 153))

    def no_longer_visible_opponent(self, event: NoLongerVisibleOpponent):
        self.visible_or_no_longer_visible_opponent(event, (255, 102, 0))

    def visible_or_no_longer_visible_opponent(
        self,
        event: typing.Union[NoLongerVisibleOpponent, NewVisibleOpponent],
        line_color,
    ) -> None:
        if self.layer_manager.debug:
            observer_actor = self.layer_manager.subject_layer.subjects_index[event.observer_subject_id]
            observed_actor = self.layer_manager.subject_layer.subjects_index[event.observed_subject_id]

            observer_pixel_position = self.layer_manager.scrolling_manager.world_to_screen(
                *self.layer_manager.grid_manager.get_world_position_of_grid_position(
                    observer_actor.subject.position,
                )
            )
            observed_pixel_position = self.layer_manager.scrolling_manager.world_to_screen(
                *self.layer_manager.grid_manager.get_world_position_of_grid_position(
                    observed_actor.subject.position,
                )
            )

            def draw_visible_opponent():
                draw_line(
                    observer_pixel_position,
                    observed_pixel_position,
                    line_color,
                )

            # TODO: Not in edit layer !
            self.layer_manager.edit_layer.append_callback(draw_visible_opponent, 1.0)

    def fire_happen(self, event: FireEvent) -> None:
        # TODO: Not in edit layer !
        shooter_actor = self.layer_manager.subject_layer.subjects_index[event.shooter_subject_id]
        shooter_pixel_position = self.layer_manager.scrolling_manager.world_to_screen(
            *self.layer_manager.grid_manager.get_world_position_of_grid_position(
                shooter_actor.subject.position,
            )
        )
        fire_to_pixel_position = self.layer_manager.scrolling_manager.world_to_screen(
            *self.layer_manager.grid_manager.get_world_position_of_grid_position(
                event.target_position,
            )
        )

        def gunshot_trace():
            draw_line(
                shooter_pixel_position,
                fire_to_pixel_position,
                color=(255, 0, 0),
            )

        def gunshot_sound():
            self.sound_lib.get_sound('gunshot_default').play()

        # To avoid all in same time
        delay = random.uniform(0.0, 0.6)

        self.layer_manager.edit_layer.append_callback(gunshot_trace, duration=0.1, delay=delay)
        self.layer_manager.edit_layer.append_callback(gunshot_sound, duration=0.0, delay=delay)

    def subject_die(self, event: DieEvent) -> None:
        killed_actor = self.layer_manager.subject_layer.subjects_index[event.shoot_subject_id]
        dead_image = pyglet.resource.image('maps/003/actors/man_d1.png')
        killed_actor.update_image(dead_image)
        killed_actor.freeze()
