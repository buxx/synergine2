# coding: utf-8
from sandbox.tile.user_action import UserAction
from synergine2.terminals import TerminalPackage
from synergine2_cocos2d.gl import draw_line
from synergine2_cocos2d.interaction import Interaction
from synergine2_xyz.move.simulation import RequestMoveBehaviour


class BaseMoveActorInteraction(Interaction):
    gui_action = None
    color = None
    request_move_behaviour_class = RequestMoveBehaviour

    def draw_pending(self) -> None:
        for actor in self.layer_manager.edit_layer.selection:
            grid_position = self.layer_manager.grid_manager.get_grid_position(actor.position)
            pixel_position = self.layer_manager.grid_manager.get_pixel_position_of_grid_position(grid_position)

            draw_line(
                self.layer_manager.scrolling_manager.world_to_screen(*pixel_position),
                self.layer_manager.edit_layer.screen_mouse,
                self.color,
            )

    def get_package_for_terminal(self) -> TerminalPackage:
        # TODO: FinishMoveEvent ?
        actions = []
        mouse_grid_position = self.layer_manager.grid_manager.get_grid_position(
            self.layer_manager.scrolling_manager.screen_to_world(
                *self.layer_manager.edit_layer.screen_mouse,
            )
        )

        for actor in self.layer_manager.edit_layer.selection:
            actions.append((
                self.request_move_behaviour_class, {
                    'subject_id': actor.subject.id,
                    'move_to': mouse_grid_position,
                    'gui_action': self.gui_action,
                }
            ))

        return TerminalPackage(
            simulation_actions=actions,
        )


class MoveActorInteraction(BaseMoveActorInteraction):
    gui_action = UserAction.ORDER_MOVE
    color = (0, 0, 255)


class MoveFastActorInteraction(BaseMoveActorInteraction):
    gui_action = UserAction.ORDER_MOVE_FAST
    color = (72, 244, 66)


class MoveCrawlActorInteraction(BaseMoveActorInteraction):
    gui_action = UserAction.ORDER_MOVE_CRAWL
    color = (235, 244, 66)
