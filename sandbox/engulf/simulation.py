# coding: utf-8
from sandbox.engulf.behaviour import GrassSpawnBehaviour
from sandbox.engulf.subject import Cell, Grass
from synergine2_xyz.xyz import XYZSubjectMixin
from synergine2_xyz.subjects import XYZSubjects
from synergine2_xyz.simulation import XYZSimulation

__author__ = 'bux'


class EngulfSubjects(XYZSubjects):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # TODO: accept multiple subjects as same position
        # TODO: init xyz with given list
        self.cell_xyz = {}
        self.grass_xyz = {}

    def remove(self, value: XYZSubjectMixin):
        super().remove(value)

        if isinstance(value, Cell):
            try:
                self.cell_xyz.get(value.position, []).remove(value)
                if not self.cell_xyz[value.position]:
                    del self.cell_xyz[value.position]
            except ValueError:
                pass

        if isinstance(value, Grass):
            del self.grass_xyz[value.position]

    def append(self, p_object: XYZSubjectMixin):
        super().append(p_object)

        if isinstance(p_object, Cell):
            self.cell_xyz.setdefault(p_object.position, []).append(p_object)

        if isinstance(p_object, Grass):
            self.grass_xyz.setdefault(p_object.position, []).append(p_object)


class Engulf(XYZSimulation):
    behaviours_classes = [
        GrassSpawnBehaviour,
    ]

    def is_possible_position(self, position: tuple) -> bool:
        top_left = (-35, -35, 0)
        bottom_right = (35, 35, 0)

        pos_x = position[0]
        pos_y = position[1]

        if pos_x < top_left[0] or pos_x > bottom_right[0]:
            return False

        if pos_y < top_left[1] or pos_y > bottom_right[1]:
            return False

        return True
