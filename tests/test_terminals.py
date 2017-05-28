# coding: utf-8
import time

from synergine2.config import Config
from synergine2.log import SynergineLogger
from synergine2.simulation import Event
from synergine2.terminals import Terminal
from synergine2.terminals import TerminalPackage
from synergine2.terminals import TerminalManager
from tests import BaseTest


class ValueTerminalPackage(TerminalPackage):
    def __init__(self, value, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.value = value


class MultiplyTerminal(Terminal):
    def receive(self, package: ValueTerminalPackage):
        self.send(ValueTerminalPackage(value=package.value * 2))
        self.send(ValueTerminalPackage(value=package.value * 4))


class DivideTerminal(Terminal):
    def receive(self, package: ValueTerminalPackage):
        self.send(ValueTerminalPackage(value=package.value / 2))
        self.send(ValueTerminalPackage(value=package.value / 4))


class AnEvent(Event):
    pass


class AnOtherEvent(Event):
    pass


class SendBackTerminal(Terminal):
    def receive(self, package: ValueTerminalPackage):
        self.send(package)


class TestTerminals(BaseTest):
    def test_terminal_communications(self):
        terminals_manager = TerminalManager(
            Config(),
            SynergineLogger('test'),
            terminals=[
                MultiplyTerminal(Config(), SynergineLogger('test')),
            ]
        )
        terminals_manager.start()
        terminals_manager.send(ValueTerminalPackage(value=42))

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
            Config(),
            SynergineLogger('test'),
            terminals=[
                MultiplyTerminal(Config(), SynergineLogger('test')),
                DivideTerminal(Config(), SynergineLogger('test')),
            ]
        )
        terminals_manager.start()
        terminals_manager.send(ValueTerminalPackage(value=42))

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

        terminals_manager.stop()  # TODO pytest must execute this if have fail

    def test_event_listen_everything(self):
        class ListenEverythingTerminal(SendBackTerminal):
            pass

        terminals_manager = TerminalManager(
            Config(),
            SynergineLogger('test'),
            terminals=[ListenEverythingTerminal(Config(), SynergineLogger('test'))]
        )
        terminals_manager.start()
        terminals_manager.send(ValueTerminalPackage(value=42))
        an_event = AnEvent(84)
        terminals_manager.send(TerminalPackage(events=[an_event]))

        # We wait max 2s (see time.sleep) to consider
        # process have finished. If not, it will fail
        packages = []
        for i in range(200):
            packages.extend(terminals_manager.receive())
            if len(packages) == 2:
                break
            time.sleep(0.01)

        assert 2 == len(packages)
        assert 42 == packages[0].value
        assert AnEvent == type(packages[1].events[0])

        terminals_manager.stop()  # TODO pytest must execute this if have fail

    def test_event_listen_specified(self):
        class ListenAnEventTerminal(SendBackTerminal):
            subscribed_events = [AnOtherEvent]

        terminals_manager = TerminalManager(
            Config(),
            SynergineLogger('test'),
            terminals=[ListenAnEventTerminal(Config(), SynergineLogger('test'))]
        )
        terminals_manager.start()
        terminals_manager.send(ValueTerminalPackage(value=42))
        an_event = AnEvent(84)
        an_other_event = AnOtherEvent(168)
        terminals_manager.send(TerminalPackage(events=[an_event, an_other_event]))

        # We wait max 10s (see time.sleep) to consider
        # process have finished. If not, it will fail
        packages = []
        for i in range(1000):
            packages.extend(terminals_manager.receive())
            if len(packages) == 2:
                break
            time.sleep(0.01)

        assert 2 == len(packages)
        assert AnOtherEvent == type(packages[1].events[0])

        terminals_manager.stop()  # TODO pytest must execute this if have fail
