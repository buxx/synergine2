# coding: utf-8
import typing

from synergine2.config import Config
from synergine2.log import SynergineLogger
from synergine2.simulation import SimulationBehaviour
from synergine2.terminals import Terminal
from synergine2.terminals import TerminalPackage
from synergine2_cocos2d.actor import Actor
from synergine2_cocos2d.exception import InteractionNotFound
from synergine2_cocos2d.gl import draw_line
from synergine2_cocos2d.layer import LayerManager
from synergine2_cocos2d.user_action import UserAction


class InteractionManager(object):
    def __init__(
        self,
        config: Config,
        logger: SynergineLogger,
        terminal: Terminal,
    ) -> None:
        self.config = config
        self.logger = logger
        self.terminal = terminal
        self.interactions = []

    def register(
        self,
        interaction_class: typing.Type['Interaction'],
        layer_manager: LayerManager,
    ) -> None:
        self.interactions.append(interaction_class(
            self.config,
            self.logger,
            terminal=self.terminal,
            layer_manager=layer_manager,
        ))

    def get_for_user_action(self, action: UserAction) -> 'Interaction':
        for interaction in self.interactions:
            if interaction.gui_action == action:
                return interaction
        raise InteractionNotFound('For action"{}"'.format(action))


class Interaction(object):
    gui_action = None  # type: UserAction

    def __init__(
        self,
        config: Config,
        logger: SynergineLogger,
        terminal: Terminal,
        layer_manager: LayerManager,
    ) -> None:
        self.config = config
        self.logger = logger
        self.terminal = terminal
        self.layer_manager = layer_manager

    def draw_pending(self) -> None:
        pass

    def execute(self) -> None:
        package = self.get_package_for_terminal()
        self.terminal.send(package)

    def get_package_for_terminal(self) -> TerminalPackage:
        raise NotImplementedError()


class BaseActorInteraction(Interaction):
    gui_action = None
    color = None

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
        actions = []
        mouse_grid_position = self.layer_manager.grid_manager.get_grid_position(
            self.layer_manager.scrolling_manager.screen_to_world(
                *self.layer_manager.edit_layer.screen_mouse,
            )
        )

        for actor in self.layer_manager.edit_layer.selection:
            behaviour_class, behaviour_data = self.get_behaviour(actor, mouse_grid_position)
            actions.append((behaviour_class, behaviour_data))

        return TerminalPackage(
            simulation_actions=actions,
        )

    def get_behaviour(self, actor: Actor, mouse_grid_position) -> typing.Tuple[typing.Type[SimulationBehaviour], dict]:
        raise NotImplementedError()
