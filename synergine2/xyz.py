# coding: utf-8
from math import sqrt
from math import degrees
from math import acos

from synergine2.simulation import SubjectMechanism, Subjects, Subject
from synergine2.simulation import Simulation as BaseSimulation


"""

Positions are exprimed as tuple: (x, y, z) Considering start point at top left:

    Z
   #
  #
 #
#-------------> X
|.
| .
|  .
|
Y
"""

COLLECTION_XYZ = 'COLLECTION_XYZ'

NORTH = 11
NORTH_EST = 12
EST = 15
SOUTH_EST = 18
SOUTH = 17
SOUTH_WEST = 16
WEST = 13
NORTH_WEST = 10

DIRECTIONS = (
    NORTH,
    NORTH_EST,
    EST,
    SOUTH_EST,
    SOUTH,
    SOUTH_WEST,
    WEST,
    NORTH_WEST,
)

DIRECTION_FROM_NORTH_DEGREES = {
    (0, 22.5): NORTH,
    (22.5, 67): NORTH_EST,
    (67, 112.5): EST,
    (112.5, 157.5): SOUTH_EST,
    (157.5, 202.5): SOUTH,
    (202.5, 247.5): SOUTH_WEST,
    (247.5, 292.5): WEST,
    (292.5, 337.5): NORTH_WEST,
    (337.5, 360): NORTH,
    (337.5, 0): NORTH
}

DIRECTION_SLIGHTLY = {
    NORTH: (NORTH_WEST, NORTH, NORTH_EST),
    NORTH_EST: (NORTH, NORTH_EST, EST),
    EST: (NORTH_EST, EST, SOUTH_EST),
    SOUTH_EST: (EST, SOUTH_EST, SOUTH),
    SOUTH: (SOUTH_EST, SOUTH, SOUTH_WEST),
    SOUTH_WEST: (SOUTH, SOUTH_WEST, WEST),
    WEST: (SOUTH_WEST, WEST, NORTH_WEST),
    NORTH_WEST: (WEST, NORTH_WEST, NORTH),
}

DIRECTION_MODIFIERS = {
    NORTH_WEST: (-1, -1, 0),
    NORTH: (0, -1, 0),
    NORTH_EST: (1, -1, 0),
    WEST: (-1, 0, 0),
    EST: (1, 0, 0),
    SOUTH_WEST: (-1, 1, 0),
    SOUTH: (0, 1, 0),
    SOUTH_EST: (1, 1, 0),
}


def get_degree_from_north(a, b):
    if a == b:
        return 0

    ax, ay = a[0], a[1]
    bx, by = b[0], b[1]
    Dx, Dy = ax, ay - 1
    ab = sqrt((bx - ax) ** 2 + (by - ay) ** 2)
    aD = sqrt((Dx - ax) ** 2 + (Dy - ay) ** 2)
    Db = sqrt((bx - Dx) ** 2 + (by - Dy) ** 2)

    degs = degrees(acos((ab ** 2 + aD ** 2 - Db ** 2) / (2 * ab * aD)))
    if bx < ax:
        return 360 - degs
    return degs


class XYZSubjectMixinMetaClass(type):
    def __init__(cls, name, parents, attribs):
        super().__init__(name, parents, attribs)
        collections = getattr(cls, "collections", [])
        if COLLECTION_XYZ not in collections:
            collections.append(COLLECTION_XYZ)


class XYZSubjectMixin(object, metaclass=XYZSubjectMixinMetaClass):
    def __init__(self, *args, **kwargs):
        """
        :param position: tuple with (x, y, z)
        """
        self._position = kwargs.pop('position')
        self.previous_direction = None
        super().__init__(*args, **kwargs)

    @property
    def position(self):
        return self._position

    @position.setter
    def position(self, value):
        self._position = value


class ProximityMixin(object):
    distance = 1
    feel_collections = [COLLECTION_XYZ]
    direction_round_decimals = 0
    distance_round_decimals = 2

    def get_for_position(
            self,
            position,
            simulation: 'XYZSimulation',
            exclude_subject: Subject=None,
    ):
        subjects = []
        for feel_collection in self.feel_collections:
            # TODO: Optimiser en calculant directement les positions alentours et
            # en regardant si elles sont occupés dans subjects.xyz par un subject
            # etant dans fell_collection
            for subject in simulation.collections.get(feel_collection, []):
                if subject == exclude_subject:
                    continue

                distance = round(
                    self.get_distance_of(
                        position=position,
                        subject=subject,
                    ),
                    self.distance_round_decimals,
                )
                if distance <= self.distance and self.acceptable_subject(subject):
                    direction = round(
                        get_degree_from_north(
                            position,
                            subject.position,
                        ),
                        self.direction_round_decimals,
                    )
                    subjects.append({
                        'subject': subject,
                        'direction': direction,
                        'distance': distance,
                    })

        return subjects

    @classmethod
    def get_distance_of(cls, position, subject: XYZSubjectMixin):
        from synergine2.xyz_utils import get_distance_between_points  # cyclic import
        return get_distance_between_points(
            position,
            subject.position,
        )

    def acceptable_subject(self, subject: Subject) -> bool:
        pass


class ProximitySubjectMechanism(ProximityMixin, SubjectMechanism):
    def run(self):
        return self.get_for_position(
            position=self.subject.position,
            simulation=self.simulation,
            exclude_subject=self.subject,
        )


class XYZSubjects(Subjects):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # TODO: accept multiple subjects as same position
        # TODO: init xyz with given list
        self.xyz = {}

    def remove(self, value: XYZSubjectMixin):
        super().remove(value)
        del self.xyz[value.position]

    def append(self, p_object: XYZSubjectMixin):
        super().append(p_object)
        self.xyz[p_object.position] = p_object


class XYZSimulation(BaseSimulation):
    accepted_subject_class = XYZSubjects


def get_direction_from_north_degree(degree: float):
    for range, direction in DIRECTION_FROM_NORTH_DEGREES.items():
        if range[0] <= degree <= range[1]:
            return direction
    raise Exception('Degree {} our of range ({})'.format(
        degree,
        DIRECTION_FROM_NORTH_DEGREES,
    ))
