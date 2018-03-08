# coding: utf-8
import typing

from synergine2.config import Config
from synergine2.simulation import SubjectComposedBehaviour
from synergine2.simulation import BehaviourStep
from synergine2.simulation import Event
from synergine2_xyz.simulation import XYZSimulation
from synergine2_xyz.subjects import XYZSubject
from tests import BaseTest


class BeginFirstEvent(Event):
    pass


class FinishFirstEvent(Event):
    pass


class BeginSecondEvent(Event):
    pass


class FinishSecondEvent(Event):
    pass


class BeginBaseEvent(Event):
    pass


class FinishBaseEvent(Event):
    pass


class MyFirstStep(BehaviourStep):
    def __init__(self, base: int, first: float=-0.5):
        self.base = base
        self.first = first

    def proceed(self) -> 'BehaviourStep':
        self.first += 0.5

        if self.first == 1:
            next_step = MySecondStep(
                base=self.base,
            )
            next_step.proceed()
            return next_step

        return self

    def generate_data(self) -> typing.Any:
        return {
            'base': self.base,
            'first': self.first,
        }

    def get_events(self) -> typing.List[Event]:
        if self.base == 0 and self.first == 0:
            return [BeginBaseEvent(), BeginFirstEvent()]

        if self.first == 0:
            return [BeginFirstEvent()]

        if self.first == 1:
            return [FinishFirstEvent(), BeginSecondEvent()]

        return []


class MySecondStep(BehaviourStep):
    def __init__(self, base: int, second: float=-0.5):
        self.base = base
        self.second = second

    def proceed(self) -> 'BehaviourStep':
        self.second += 0.5

        if self.second == 1:
            self.base = 1

        return self

    def get_events(self) -> typing.List[Event]:
        if self.second == 0:
            return [BeginSecondEvent(), FinishFirstEvent()]

        if self.second == 1:
            return [FinishSecondEvent(), FinishBaseEvent()]

        return []

    def generate_data(self) -> typing.Any:
        return {
            'base': self.base,
            'second': self.second,
        }


class MyComposedBehaviour(SubjectComposedBehaviour):
    step_classes = [
        (MySecondStep, lambda d: 'second' in d),
        (MyFirstStep, lambda d: 'first' in d or d.get('base') == 0),
    ]


class TestComposedBehaviour(BaseTest):
    def test_subject_composed_behaviour(self):
        config = Config({})
        simulation = XYZSimulation(config)
        subject = XYZSubject(config, simulation)

        my_composed_behaviour = MyComposedBehaviour(
            config=config,
            simulation=simulation,
            subject=subject,
        )

        # Thirst cycle, ThirstStep is reached and produce event
        data = my_composed_behaviour.run({
            'base': 0,
        })
        assert {'base': 0, 'first': 0} == data

        events = my_composed_behaviour.action(data)
        assert events
        assert 2 == len(events)
        assert isinstance(events[0], BeginBaseEvent)
        assert isinstance(events[1], BeginFirstEvent)

        # Second cycle (with previous cycle data), there is data but no events
        data = my_composed_behaviour.run(data)
        assert {'base': 0, 'first': 0.5} == data

        events = my_composed_behaviour.action(data)
        assert not events

        # Third cycle (still with previous cycle data) there is data but and events
        data = my_composed_behaviour.run(data)
        assert {'base': 0, 'second': 0} == data

        events = my_composed_behaviour.action(data)
        assert events
        assert 2 == len(events)
        assert isinstance(events[0], BeginSecondEvent)
        assert isinstance(events[1], FinishFirstEvent)

        # Fourth cycle (still with previous cycle data) there is data but no events
        data = my_composed_behaviour.run(data)
        assert {'base': 0, 'second': 0.5} == data

        events = my_composed_behaviour.action(data)
        assert not events

        # Cycle 5 (still with previous cycle data) there is data and events
        data = my_composed_behaviour.run(data)
        assert {'base': 1, 'second': 1} == data

        events = my_composed_behaviour.action(data)
        assert events
        assert 2 == len(events)
        assert isinstance(events[0], FinishSecondEvent)
        assert isinstance(events[1], FinishBaseEvent)
