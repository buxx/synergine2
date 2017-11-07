# coding: utf-8
import time

from sandbox.tile.user_action import UserAction
from synergine2.config import Config
from synergine2.simulation import Simulation
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
