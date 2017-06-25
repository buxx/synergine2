# coding: utf-8
from synergine2.simulation import Subject
from synergine2.xyz import XYZSimulation
from synergine2.xyz import XYZSubjectMixin
from synergine2.xyz import XYZSubjects


class TileStrategySimulation(XYZSimulation):
    behaviours_classes = [

    ]


class TileStrategySubjects(XYZSubjects):
    pass


class BaseSubject(XYZSubjectMixin, Subject):
    pass
