# coding: utf-8
import typing

from synergine2.config import Config
from synergine2.log import SynergineLogger
from synergine2.terminals import Terminal
from synergine2.terminals import TerminalPackage
from synergine2_cocos2d.exception import InteractionNotFound
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
