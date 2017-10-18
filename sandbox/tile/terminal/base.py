# coding: utf-8
from sandbox.tile.simulation.subject import Man as ManSubject
from sandbox.tile.gui.actor import Man as ManActor
from synergine2_cocos2d.terminal import GameTerminal
from synergine2_xyz.move import FinishMoveEvent
from synergine2_xyz.move import StartMoveEvent


class CocosTerminal(GameTerminal):
    subscribed_events = [
        FinishMoveEvent,
        StartMoveEvent,
    ]

    def __init__(self, *args, asynchronous: bool, map_dir_path: str, **kwargs):
        super().__init__(*args, **kwargs)
        self.asynchronous = asynchronous
        self.map_dir_path = map_dir_path

    def run(self):
        from sandbox.tile.gui.base import Game
        from synergine2_cocos2d.gui import SubjectMapper

        self.gui = Game(
            self.config,
            self.logger,
            self,
            map_dir_path=self.map_dir_path,
        )

        # TODO: Defind on some other place ?
        self.gui.subject_mapper_factory.register_mapper(
            ManSubject,
            SubjectMapper(ManActor),
        )

        self.gui.run()
