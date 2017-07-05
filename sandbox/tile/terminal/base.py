# coding: utf-8

from synergine2.terminals import Terminal


class CocosTerminal(Terminal):
    subscribed_events = [

    ]

    def __init__(self, *args, asynchronous: bool, map_dir_path: str, **kwargs):
        super().__init__(*args, **kwargs)
        self.asynchronous = asynchronous
        self.gui = None
        self.map_dir_path = map_dir_path

    def run(self):
        from sandbox.tile.gui.base import Game
        self.gui = Game(
            self.config,
            self.logger,
            self,
            map_dir_path=self.map_dir_path,
        )
        self.gui.run()
