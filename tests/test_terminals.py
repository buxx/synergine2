import time

from synergine2.terminals import Terminal
from synergine2.terminals import TerminalPackage
from synergine2.terminals import TerminalManager
from tests import BaseTest


class MultiplyTerminal(Terminal):
    def receive(self, package: TerminalPackage):
        self.send(TerminalPackage(package.value * 2))
        self.send(TerminalPackage(package.value * 4))


class DivideTerminal(Terminal):
    def receive(self, package: TerminalPackage):
        self.send(TerminalPackage(package.value / 2))
        self.send(TerminalPackage(package.value / 4))


class TestTerminals(BaseTest):
    def test_terminal_communications(self):
        terminals_manager = TerminalManager(
            terminals=[
                MultiplyTerminal(),
            ]
        )
        terminals_manager.start()
        terminals_manager.send(TerminalPackage(42))

        # We wait max 2s (see time.sleep) to consider
        # process have finished. If not, it will fail
        packages = []
        for i in range(200):
            packages.extend(terminals_manager.receive())
            if len(packages) == 2:
                break
            time.sleep(0.01)

        assert 2 == len(packages)
        values = [p.value for p in packages]
        assert 84 in values
        assert 168 in values

        terminals_manager.stop()  # pytest must execute this if have fail

    def test_terminals_communications(self):
        terminals_manager = TerminalManager(
            terminals=[
                MultiplyTerminal(),
                DivideTerminal(),
            ]
        )
        terminals_manager.start()
        terminals_manager.send(TerminalPackage(42))

        # We wait max 2s (see time.sleep) to consider
        # process have finished. If not, it will fail
        packages = []
        for i in range(200):
            packages.extend(terminals_manager.receive())
            if len(packages) == 4:
                break
            time.sleep(0.01)

        assert 4 == len(packages)
        values = [p.value for p in packages]
        assert 84 in values
        assert 168 in values
        assert 21 in values
        assert 10.5 in values

        terminals_manager.stop()  # pytest must execute this if have fail
