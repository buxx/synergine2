# coding: utf-8
from sandbox.engulf.subject import Cell, Grass
from synergine2.xyz import XYZSubjects, XYZSubjectMixin

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
            del self.cell_xyz[value.position]

        if isinstance(value, Grass):
            del self.grass_xyz[value.position]

    def append(self, p_object: XYZSubjectMixin):
        super().append(p_object)

        if isinstance(p_object, Cell):
            self.cell_xyz[p_object.position] = p_object

        if isinstance(p_object, Grass):
            self.grass_xyz[p_object.position] = p_object
