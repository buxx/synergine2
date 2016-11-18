import time

from synergine2.terminals import Terminal
from synergine2.terminals import TerminalManager
from tests import BaseTest


class MultiplyTerminal(Terminal):
    def receive(self, value):
        self.send(value * 2)
        self.send(value * 4)


class DivideTerminal(Terminal):
    def receive(self, value):
        self.send(value / 2)
        self.send(value / 4)


class TestTerminals(BaseTest):
    def test_terminal_communications(self):
        terminals_manager = TerminalManager(
            terminals=[
                MultiplyTerminal(),
            ]
        )
        terminals_manager.start()
        terminals_manager.send(42)

        # We wait max 2s (see time.sleep) to consider
        # process have finished. If not, it will fail
        values = []
        for i in range(200):
            values.extend(terminals_manager.receive())
            if len(values) == 2:
                break
            time.sleep(0.01)

        assert 2 == len(values)
        values = [v for v in values]
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
        terminals_manager.send(42)

        # We wait max 2s (see time.sleep) to consider
        # process have finished. If not, it will fail
        values = []
        for i in range(200):
            values.extend(terminals_manager.receive())
            if len(values) == 4:
                break
            time.sleep(0.01)

        assert 4 == len(values)
        values = [v for v in values]
        assert 84 in values
        assert 168 in values
        assert 21 in values
        assert 10.5 in values

        terminals_manager.stop()  # pytest must execute this if have fail
