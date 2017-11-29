# coding: utf-8
import random
import time
import typing

from sandbox.tile.const import COLLECTION_ALIVE
from sandbox.tile.simulation.base import AliveSubjectBehaviour
from sandbox.tile.simulation.event import NoLongerVisibleOpponent
from sandbox.tile.simulation.event import FireEvent
from sandbox.tile.simulation.event import DieEvent
from sandbox.tile.simulation.event import NewVisibleOpponent
from sandbox.tile.simulation.mechanism import OpponentVisibleMechanism
from sandbox.tile.user_action import UserAction
from synergine2.config import Config
from synergine2.simulation import Simulation
from synergine2.simulation import Event
from synergine2.simulation import Subject
from synergine2_xyz.move.simulation import MoveToBehaviour as BaseMoveToBehaviour


class MoveToBehaviour(BaseMoveToBehaviour):
    def __init__(
        self,
        config: Config,
        simulation: Simulation,
        subject: Subject,
    ) -> None:
        super().__init__(config, simulation, subject)
        self._walk_duration = float(self.config.resolve('game.move.walk_ref_time'))
        self._run_duration = float(self.config.resolve('game.move.run_ref_time'))
        self._crawl_duration = float(self.config.resolve('game.move.crawl_ref_time'))

    def is_terminated(self) -> bool:
        return COLLECTION_ALIVE not in self.subject.collections

    def _can_move_to_next_step(self, move_to_data: dict) -> bool:
        if move_to_data['gui_action'] == UserAction.ORDER_MOVE:
            return time.time() - move_to_data['last_intention_time'] >= self._walk_duration
        if move_to_data['gui_action'] == UserAction.ORDER_MOVE_FAST:
            return time.time() - move_to_data['last_intention_time'] >= self._run_duration
        if move_to_data['gui_action'] == UserAction.ORDER_MOVE_CRAWL:
            return time.time() - move_to_data['last_intention_time'] >= self._crawl_duration


class LookAroundBehaviour(AliveSubjectBehaviour):
    """
    Behaviour who permit to reference visible things like enemies
    """
    visible_mechanism = OpponentVisibleMechanism
    use = [visible_mechanism]

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._seconds_frequency = float(self.config.resolve('game.look_around.frequency'))

    @property
    def seconds_frequency(self) -> typing.Optional[float]:
        return self._seconds_frequency

    def action(self, data) -> [Event]:
        new_visible_subject_events = []
        no_longer_visible_subject_events = []

        for no_longer_visible_subject_id in data['no_longer_visible_subject_ids']:
            no_longer_visible_subject_events.append(NoLongerVisibleOpponent(
                observer_subject_id=self.subject.id,
                observed_subject_id=no_longer_visible_subject_id,
            ))
            self.subject.visible_opponent_ids.remove(no_longer_visible_subject_id)

        for new_visible_subject_id in data['new_visible_subject_ids']:
            new_visible_subject_events.append(NewVisibleOpponent(
                observer_subject_id=self.subject.id,
                observed_subject_id=new_visible_subject_id,
            ))
            self.subject.visible_opponent_ids.append(new_visible_subject_id)

        return new_visible_subject_events + no_longer_visible_subject_events

    def run(self, data):
        visible_subjects = data[self.visible_mechanism]['visible_subjects']
        visible_subject_ids = [s.id for s in visible_subjects]
        new_visible_subject_ids = []
        no_longer_visible_subject_ids = []

        for subject_id in self.subject.visible_opponent_ids:
            if subject_id not in visible_subject_ids:
                no_longer_visible_subject_ids.append(subject_id)

        for subject in visible_subjects:
            if subject.id not in self.subject.visible_opponent_ids:
                new_visible_subject_ids.append(subject.id)

        return {
            'new_visible_subject_ids': new_visible_subject_ids,
            'no_longer_visible_subject_ids': no_longer_visible_subject_ids,
        }


class EngageOpponent(AliveSubjectBehaviour):
    visible_mechanism = OpponentVisibleMechanism
    use = [visible_mechanism]

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._seconds_frequency = float(self.config.resolve('game.engage.frequency'))

    @property
    def seconds_frequency(self) -> typing.Optional[float]:
        return self._seconds_frequency

    def action(self, data) -> [Event]:
        kill = data['kill']
        target_subject_id = data['target_subject_id']
        target_subject = self.simulation.subjects.index[target_subject_id]
        target_position = data['target_position']

        events = list()
        events.append(FireEvent(shooter_subject_id=self.subject.id, target_position=target_position))

        if kill:
            target_subject.collections.remove(COLLECTION_ALIVE)
            # FIXME: Must be automatic when manipulate subject collections !
            self.simulation.collections[COLLECTION_ALIVE].remove(target_subject_id)
            self.simulation.collections[COLLECTION_ALIVE] = self.simulation.collections[COLLECTION_ALIVE]
            events.append(DieEvent(shooter_subject_id=self.subject.id, shoot_subject_id=target_subject_id))

        return events

    def run(self, data):
        visible_subjects = data[self.visible_mechanism]['visible_subjects']
        if not visible_subjects:
            return
        # Manage selected target (can change, better visibility, etc ...)
        # Manage weapon munition to be able to fire
        # Manage fear/under fire ...
        # Manage weapon reload time

        # For dev fun, don't fire at random
        if random.randint(1, 3) == -1:
            # Executed but decided to fail
            self.last_execution_time = time.time()
            return False

        target_subject = random.choice(visible_subjects)
        kill = random.randint(0, 100) >= 75

        # Manage fire miss or touch (visibility, fear, opponent hiding, etc ...)
        return {
            'kill': kill,
            'target_subject_id': target_subject.id,
            'target_position': target_subject.position,
        }
