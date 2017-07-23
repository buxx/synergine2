# coding: utf-8
import typing

from synergine2.simulation import Simulation as BaseSimulation
from synergine2_xyz.xyz import XYZSubject
from synergine2_xyz.subjects import XYZSubjects


class XYZSimulation(BaseSimulation):
    accepted_subject_class = XYZSubjects

    def is_possible_subject_position(self, subject: XYZSubject, position: tuple) -> bool:
        return self.is_possible_position(position)

    def is_possible_position(self, position: tuple) -> bool:
        return True
