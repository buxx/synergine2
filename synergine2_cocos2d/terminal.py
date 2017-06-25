# coding: utf-8
from synergine2.terminals import Terminal, TerminalPackage


class GameTerminal(Terminal):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.gui = None

    def receive(self, package: TerminalPackage):
        self.gui.before_received(package)
        super().receive(package)
        self.gui.after_received(package)

    def run(self):
        raise NotImplementedError()
