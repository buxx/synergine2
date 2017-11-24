# coding: utf-8
import typing

from sandbox.tile.const import SIDE
from synergine2_xyz.subjects import XYZSubject
from synergine2_xyz.visible.simulation import VisibleMechanism


class OpponentVisibleMechanism(VisibleMechanism):
    def reduce_subjects(self, subjects: typing.List[XYZSubject]) -> typing.Iterator[XYZSubject]:
        def is_opponent(subject: XYZSubject) -> bool:
            return self.subject.properties[SIDE] != subject.properties[SIDE]

        return filter(is_opponent, subjects)
