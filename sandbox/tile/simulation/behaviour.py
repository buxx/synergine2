# coding: utf-8
import time

from sandbox.tile.simulation.event import NoLongerVisibleOpponent
from sandbox.tile.simulation.event import NewVisibleOpponent
from sandbox.tile.simulation.mechanism import OpponentVisibleMechanism
from sandbox.tile.user_action import UserAction
from synergine2.config import Config
from synergine2.simulation import Simulation
from synergine2.simulation import SubjectBehaviour
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

    def _can_move_to_next_step(self, move_to_data: dict) -> bool:
        if move_to_data['gui_action'] == UserAction.ORDER_MOVE:
            return time.time() - move_to_data['last_intention_time'] >= self._walk_duration
        if move_to_data['gui_action'] == UserAction.ORDER_MOVE_FAST:
            return time.time() - move_to_data['last_intention_time'] >= self._run_duration
        if move_to_data['gui_action'] == UserAction.ORDER_MOVE_CRAWL:
            return time.time() - move_to_data['last_intention_time'] >= self._crawl_duration


class LookAroundBehaviour(SubjectBehaviour):
    """
    Behaviour who permit to reference visible things like enemies
    """
    visible_mechanism = OpponentVisibleMechanism
    use = [visible_mechanism]
    force_action = True

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
