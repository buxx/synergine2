# coding: utf-8

from pyglet.window import key

from cocos.actions import MoveTo as BaseMoveTo
from sandbox.tile.simulation.physics import TilePhysics
from sandbox.tile.user_action import UserAction
from synergine2.config import Config
from synergine2.log import SynergineLogger
from synergine2.terminals import Terminal
from synergine2_cocos2d.actions import MoveTo
# TODO NOW: MOVE
from synergine2_cocos2d.animation import ANIMATION_CRAWL
from synergine2_cocos2d.animation import ANIMATION_WALK
from synergine2_cocos2d.animation import Animate
from synergine2_cocos2d.gui import EditLayer as BaseEditLayer
from synergine2_cocos2d.gui import TMXGui
from synergine2_cocos2d.layer import LayerManager
from synergine2_xyz.move.simulation import FinishMoveEvent
from synergine2_xyz.move.simulation import StartMoveEvent
from synergine2_xyz.physics import Matrixes
from synergine2_xyz.utils import get_angle


class EditLayer(BaseEditLayer):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.matrixes = Matrixes()
        self.physics = TilePhysics(
            self.config,
            map_file_path='sandbox/tile/maps/003/003.tmx',  # FIXME: HARDCODED
        )

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


class Game(TMXGui):
    layer_manager_class = TileLayerManager

    def __init__(
        self,
        config: Config,
        logger: SynergineLogger,
        terminal: Terminal,
        read_queue_interval: float = 1 / 60.0,
        map_dir_path: str=None,
    ):
        super().__init__(
            config,
            logger,
            terminal,
            read_queue_interval,
            map_dir_path,
        )

        self.terminal.register_event_handler(
            FinishMoveEvent,
            self.set_subject_position,
        )

        self.terminal.register_event_handler(
            StartMoveEvent,
            self.start_move_subject,
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
        new_world_position = self.layer_manager.grid_manager.get_pixel_position_of_grid_position(event.to_position)

        actor.stop_actions((BaseMoveTo,))
        actor.set_position(*new_world_position)

    def start_move_subject(self, event: StartMoveEvent):
        actor = self.layer_manager.subject_layer.subjects_index[event.subject_id]
        new_world_position = self.layer_manager.grid_manager.get_pixel_position_of_grid_position(event.to_position)

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
