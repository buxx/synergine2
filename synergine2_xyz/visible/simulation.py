# coding: utf-8
import typing

from synergine2.config import Config
from synergine2.simulation import SubjectMechanism, Simulation, Subject
from synergine2_xyz.simulation import XYZSimulation
from synergine2_xyz.subjects import XYZSubject


class VisibleMechanism(SubjectMechanism):
    from_collection = None

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

    def _get_subject_iterable_from_collection(self, collection_name: str) -> typing.Iterator[XYZSubject]:
        for subject_id in self.simulation.collections[collection_name]:
            yield self.simulation.subjects.index[subject_id]

    def run(self) -> dict:
        if self.from_collection is None:
            subjects = self.simulation.subjects
        else:
            subjects = self._get_subject_iterable_from_collection(self.from_collection)

        subjects_to_parse = self.reduce_subjects(subjects)
        subjects_visible = list(filter(self.is_visible, subjects_to_parse))
        return {
            'visible_subjects': subjects_visible,
        }
