# coding: utf-8
import typing

from synergine2.config import Config
from synergine2.simulation import SimulationBehaviour, SubjectBehaviour
from synergine2.simulation import Intention
from synergine2.simulation import Simulation
from synergine2.simulation import Event
from synergine2_xyz.simulation import XYZSimulation


class MoveToIntention(Intention):
    def __init__(self, move_to: typing.Tuple[int, int]) -> None:
        self.move_to = move_to
        self.path = []  # type: typing.List[typing.Tuple[int, int]]
        self.path_progression = None  # type: int


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
            subject.intentions.append(self.move_intention_class(move_to))
        except KeyError:
            # TODO: log error here
            pass

        return []


class MoveToBehaviour(SubjectBehaviour):
    def run(self, data):
        # TODO: progresser dans l'intention (comment implementer ça?)
        raise NotImplementedError()

    def action(self, data) -> [Event]:
        # TODO: effectuer un move vers une nouvelle position ou faire progresser "l'entre-deux"
        raise NotImplementedError()
