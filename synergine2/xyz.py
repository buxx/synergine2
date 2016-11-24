from math import sqrt
from math import degrees
from math import acos

from synergine2.simulation import Mechanism, Subjects
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


def get_distance_between_points(a: tuple, b: tuple) -> float:
    return abs(sqrt((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2))


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
        self.position = kwargs.pop('position')
        super().__init__(*args, **kwargs)


class ProximityMechanism(Mechanism):
    distance = 1
    feel_collections = [COLLECTION_XYZ]
    direction_round_decimals = 0
    distance_round_decimals = 2

    def run(self):
        subjects = []
        for feel_collection in self.feel_collections:
            for subject in self.simulation.collections.get(feel_collection, []):
                if subject == self.subject:
                    continue

                distance = round(
                    self.get_distance_of(subject),
                    self.distance_round_decimals,
                )
                if subject != self.subject and distance <= self.distance:
                    direction = round(
                        get_degree_from_north(
                            self.subject.position,
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

    def get_distance_of(self, subject: XYZSubjectMixin):
        return get_distance_between_points(
            self.subject.position,
            subject.position,
        )


class XYZSubjects(Subjects):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # TODO: accept multiple subjects as same position
        self.xyz = {}

    def remove(self, value: XYZSubjectMixin):
        super().remove(value)
        del self.xyz[value.position]

    def append(self, p_object: XYZSubjectMixin):
        super().append(p_object)
        self.xyz[p_object.position] = p_object


class Simulation(BaseSimulation):
    accepted_subject_class = XYZSubjects
