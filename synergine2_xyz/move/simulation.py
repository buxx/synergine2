# coding: utf-8
import time
import typing

from synergine2.config import Config
from synergine2.simulation import SimulationBehaviour
from synergine2.simulation import Simulation
from synergine2.simulation import Event
from synergine2_xyz.move.intention import MoveToIntention
from synergine2_xyz.simulation import XYZSimulation


class RequestMoveBehaviour(SimulationBehaviour):
    move_intention_class = MoveToIntention

    @classmethod
    def merge_data(cls, new_data, start_data=None):
        # TODO: behaviour/Thing dedicated to Gui -> Simulation ?
        pass  # This behaviour is designed to be launch by terminal

    def __init__(
        self,
        config: Config,
        simulation: Simulation,
    ):
        super().__init__(config, simulation)
        self.simulation = typing.cast(XYZSimulation, self.simulation)

    def run(self, data):
        # TODO: behaviour/Thing dedicated to Gui -> Simulation ?
        pass  # This behaviour is designed to be launch by terminal

    def action(self, data) -> typing.List[Event]:
        subject_id = data['subject_id']
        move_to = data['move_to']

        try:
            subject = self.simulation.subjects.index[subject_id]
            subject.intentions.set(self.move_intention_class(
                move_to,
                gui_action=data['gui_action'],
            ))
        except KeyError:
            # TODO: log error here
            pass

        return []
