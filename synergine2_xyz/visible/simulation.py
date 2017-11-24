# coding: utf-8
import typing

from synergine2.config import Config
from synergine2.simulation import SubjectMechanism, Simulation, Subject
from synergine2_xyz.simulation import XYZSimulation
from synergine2_xyz.subjects import XYZSubject


class VisibleMechanism(SubjectMechanism):
    def __init__(
        self,
        config: Config,
        simulation: Simulation,
        subject: Subject,
    ) -> None:
        super().__init__(config, simulation, subject)
        self.simulation = typing.cast(XYZSimulation, self.simulation)
        self.subject = typing.cast(XYZSubject, self.subject)

    def reduce_subjects(self, subjects: typing.List[XYZSubject]) -> typing.Iterator[XYZSubject]:
        return subjects

    def is_visible(self, observed: XYZSubject) -> bool:
        return self.simulation.physics.subject_see_subject(self.subject, observed)

    def run(self) -> dict:
        subjects_to_parse = self.reduce_subjects(self.simulation.subjects)
        subjects_visible = list(filter(self.is_visible, subjects_to_parse))
        return {
            'visible_subjects': subjects_visible,
        }
