# coding: utf-8
import time

from freezegun import freeze_time

from synergine2.config import Config
from synergine2.simulation import Simulation, Subject
from synergine2_cocos2d.user_action import UserAction as BaseUserAction
from synergine2_xyz.move.intention import MoveToIntention
from synergine2_xyz.move.simulation import MoveToMechanism
from synergine2_xyz.move.simulation import StartMoveEvent
from synergine2_xyz.move.simulation import FinishMoveEvent
from synergine2_xyz.simulation import XYZSimulation
from synergine2_xyz.subjects import XYZSubject
from tests import BaseTest
from synergine2_xyz.move.simulation import MoveToBehaviour as BaseMoveToBehaviour


class MyMoveToBehaviour(BaseMoveToBehaviour):
    def __init__(
        self,
        config: Config,
        simulation: Simulation,
        subject: Subject,
    ) -> None:
        super().__init__(config, simulation, subject)
        self._walk_duration = float(self.config.resolve('game.move.walk_ref_time'))

    def _can_move_to_next_step(self, move_to_data: dict) -> bool:
        if move_to_data['gui_action'] == UserAction.ORDER_MOVE:
            return time.time() - move_to_data['last_intention_time'] >= self._walk_duration


class UserAction(BaseUserAction):
    ORDER_MOVE = 'ORDER_MOVE'


class MySubject(XYZSubject):
    pass


class MySimulation(XYZSimulation):
    pass


class TestMove(BaseTest):
    def test_behaviour_cycle(self):
        config = Config({
            'game': {
                'move': {
                    'walk_ref_time': 2,
                }
            }
        })
        simulation = MySimulation(config)
        subject = MySubject(config, simulation)
        behaviour = MyMoveToBehaviour(config, simulation, subject)

        with freeze_time("2000-01-01 00:00:00"):
            move_intention = MoveToIntention((0, 3), time.time(), gui_action=UserAction.ORDER_MOVE)

            assert move_intention.path_progression == -1
            assert move_intention.just_reach is False
            assert move_intention.initial is True

            subject.intentions.set(move_intention)
            move_data = {
                'new_path': [(0, 1), (0, 2)],
                'last_intention_time': time.time(),
                'just_reach': False,
                'initial': True,
                'gui_action': UserAction.ORDER_MOVE,
            }
            data = {
                MoveToMechanism: move_data,
            }
            run_data = behaviour.run(data)

            assert move_data == run_data
            events = behaviour.action(run_data)

        assert events
        assert 1 == len(events)
        assert isinstance(events[0], StartMoveEvent)

        assert move_intention.path_progression == -1
        assert move_intention.just_reach is False
        assert move_intention.initial is False

        # Update data like mechanism do it
        move_data['last_intention_time'] = move_intention.last_intention_time
        move_data['just_reach'] = move_intention.just_reach
        move_data['initial'] = move_intention.initial

        # Only one second, no reach
        with freeze_time("2000-01-01 00:00:01"):
            run_data = behaviour.run(data)

        assert run_data is False

        # Two second, step reach
        with freeze_time("2000-01-01 00:00:02"):
            run_data = behaviour.run(data)

            assert {
                       'new_path': [(0, 1), (0, 2)],
                       'initial': False,
                       'just_reach': False,
                       'last_intention_time': 946684800.0,
                       'reach_next': True,
                       'gui_action': UserAction.ORDER_MOVE,
                   } == run_data

            events = behaviour.action(run_data)

            assert events
            assert 1 == len(events)
            assert isinstance(events[0], FinishMoveEvent)

        # Update data like mechanism do it
        move_data['last_intention_time'] = move_intention.last_intention_time
        move_data['just_reach'] = move_intention.just_reach
        move_data['initial'] = move_intention.initial

        # Three seconds, start a new move
        with freeze_time("2000-01-01 00:00:03"):
            run_data = behaviour.run(data)

            assert {
                       'new_path': [(0, 1), (0, 2)],
                       'initial': False,
                       'just_reach': True,
                       'last_intention_time': 946684802.0,
                       'reach_next': False,
                       'gui_action': UserAction.ORDER_MOVE,
                   } == run_data

            events = behaviour.action(run_data)

            assert events
            assert 1 == len(events)
            assert isinstance(events[0], StartMoveEvent)

        # Update data like mechanism do it
        move_data['last_intention_time'] = move_intention.last_intention_time
        move_data['just_reach'] = move_intention.just_reach
        move_data['initial'] = move_intention.initial

        # Four seconds, start a new move
        with freeze_time("2000-01-01 00:00:04"):
            run_data = behaviour.run(data)

            assert {
                       'new_path': [(0, 1), (0, 2)],
                       'initial': False,
                       'just_reach': False,
                       'last_intention_time': 946684802.0,
                       'reach_next': True,
                       'gui_action': UserAction.ORDER_MOVE,
                   } == run_data

            events = behaviour.action(run_data)

            assert events
            assert 1 == len(events)
            assert isinstance(events[0], FinishMoveEvent)
