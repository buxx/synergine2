# coding: utf-8
import typing
from math import acos
from math import degrees
from math import sqrt

from synergine2.exceptions import SynergineException
from synergine2.share import shared
from synergine2.simulation import Subject

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


class XYZException(SynergineException):
    pass


class PositionNotPossible(XYZException):
    pass


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
        collections = getattr(cls, "start_collections", [])
        if COLLECTION_XYZ not in collections:
            collections.append(COLLECTION_XYZ)


class XYZSubjectMixin(object, metaclass=XYZSubjectMixinMetaClass):
    position = shared.create_self('position', lambda: (0, 0, 0))

    def __init__(self, *args, **kwargs):
        """
        :param position: tuple with (x, y, z)
        """
        position = None
        try:
            position = kwargs.pop('position')
        except KeyError:
            pass

        self.previous_direction = None  # TODO: shared
        super().__init__(*args, **kwargs)

        if position:
            self.position = position


class ProximityMixin(object):
    distance = 1
    feel_collections = [COLLECTION_XYZ]
    direction_round_decimals = 0
    distance_round_decimals = 2

    def have_to_check_position_is_possible(self) -> bool:
        return True

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
            for subject_id in simulation.collections.get(feel_collection, []):
                subject = simulation.get_or_create_subject(subject_id)
                if subject.id == exclude_subject.id:
                    continue

                if self.have_to_check_position_is_possible() and not simulation.is_possible_position(subject.position):
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
                        'subject_id': subject.id,
                        'direction': direction,
                        'distance': distance,
                    })

        return subjects

    @classmethod
    def get_distance_of(cls, position, subject: XYZSubjectMixin):
        from synergine2_xyz.utils import get_distance_between_points  # cyclic import
        return get_distance_between_points(
            position,
            subject.position,
        )

    def acceptable_subject(self, subject: Subject) -> bool:
        return True


def get_direction_from_north_degree(degree: float):
    for range, direction in DIRECTION_FROM_NORTH_DEGREES.items():
        if range[0] <= degree <= range[1]:
            return direction
    raise Exception('Degree {} out of range ({})'.format(
        degree,
        DIRECTION_FROM_NORTH_DEGREES,
    ))


def get_neighbor_positions(position: typing.Tuple[int, int]) -> typing.List[typing.Tuple[int, int]]:
    neighbors = []

    for modifier_x, modifier_y, modifier_z in DIRECTION_MODIFIERS.values():
        neighbors.append((position[0] + modifier_x, position[1] + modifier_y))

    return neighbors
