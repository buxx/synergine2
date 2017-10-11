# coding: utf-8
from synergine2.simulation import SubjectMechanism
from synergine2_xyz.xyz import ProximityMixin


class ProximitySubjectMechanism(ProximityMixin, SubjectMechanism):
    def run(self):
        return self.get_for_position(
            position=self.subject.position,
            simulation=self.simulation,
            exclude_subject=self.subject,
        )
