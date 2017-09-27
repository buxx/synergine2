# coding: utf-8
from synergine2.config import Config
from synergine2.simulation import Simulation as BaseSimulation
from synergine2_xyz.physics import Physics
from synergine2_xyz.subjects import XYZSubjects
from synergine2_xyz.subjects import XYZSubject


class XYZSimulation(BaseSimulation):
    accepted_subject_class = XYZSubjects

    def __init__(
        self,
        config: Config,
    ) -> None:
        super().__init__(config)

        self.physics = self.create_physics()
        self.physics.load()

    def create_physics(self) -> Physics:
        return Physics(self.config)

    def is_possible_subject_position(self, subject: XYZSubject, position: tuple) -> bool:
        return self.is_possible_position(position)

    def is_possible_position(self, position: tuple) -> bool:
        return True
