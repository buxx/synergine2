import time

from synergine2.terminals import Terminal
from synergine2.terminals import TerminalPackage
from synergine2.terminals import TerminalManager
from tests import BaseTest


class FakeTerminal(Terminal):
    def receive(self, package: TerminalPackage):
        self.send(TerminalPackage(package.value * 2))
        self.send(TerminalPackage(package.value * 4))


class TestTerminals(BaseTest):
    def test_terminals_communications(self):
        terminals_manager = TerminalManager(
            terminals=[
                FakeTerminal(),
            ]
        )
        terminals_manager.start()
        terminals_manager.send(TerminalPackage(42))

        # We wait max 2s (see time.sleep) to consider
        # process have finished. If not, it will fail
        for i in range(200):
            packages = terminals_manager.receive()
            if packages:
                break
            time.sleep(0.01)

        assert 2 == len(packages)
        values = [p.value for p in packages]
        assert 84 in values
        assert 168 in values

        terminals_manager.stop()  # pytest must execute this if have fail
        # TODO: Tester avec plusieurs terminaux
