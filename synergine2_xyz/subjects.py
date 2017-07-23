# coding: utf-8
from synergine2.simulation import Subjects
from synergine2_xyz.xyz import XYZSubjectMixin, PositionNotPossible


class XYZSubjects(Subjects):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # TODO: accept multiple subjects as same position
        # TODO: init xyz with given list
        self.xyz = {}

    def have_to_check_position_is_possible(self) -> bool:
        return True

    def remove(self, value: XYZSubjectMixin):
        super().remove(value)

        try:
            self.xyz.get(value.position, []).remove(value)
            if not self.xyz[value.position]:
                del self.xyz[value.position]
        except ValueError:
            pass

    def append(self, p_object: XYZSubjectMixin):
        super().append(p_object)

        if self.have_to_check_position_is_possible() \
           and not self.simulation.is_possible_subject_position(p_object, p_object.position):
            raise PositionNotPossible('Position {} for {} is not possible'.format(
                str(p_object.position),
                str(p_object),
            ))

        self.xyz.setdefault(p_object.position, []).append(p_object)