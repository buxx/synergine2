# coding: utf-8
from synergine2.terminals import Terminal
from synergine2.terminals import TerminalPackage


class GameTerminal(Terminal):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.gui = None

    def receive(self, package: TerminalPackage):
        self.gui.before_received(package)
        # TODO: pas d'event après le move: il faut subscribe je crois :p
        super().receive(package)
        self.gui.after_received(package)

    def run(self):
        raise NotImplementedError()
