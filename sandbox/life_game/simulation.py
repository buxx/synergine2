from synergine2.simulation import Subject
from synergine2.simulation import Behaviour
from synergine2.xyz import ProximityMechanism
from synergine2.xyz import XYZSubjectMixin

COLLECTION_CELL = 'COLLECTION_CELL'  # Collections of Cell type


class CellProximityMechanism(ProximityMechanism):
    distance = 1.41  # distance when on angle
    feel_collections = [COLLECTION_CELL]


class CellDieBehaviour(Behaviour):
    use = [CellProximityMechanism]

    def run(self, data):
        around_count = len(data[CellProximityMechanism])
        if around_count in [2, 3]:
            return False
        # If we return around_count, when around_count is 0,
        # cycle manager will consider as False
        return True

    def action(self, data):
        new_empty = Empty(
            simulation=self.simulation,
            position=self.subject.position,
        )
        self.simulation.subjects.remove(self.subject)
        self.simulation.subjects.append(new_empty)


class CellBornBehaviour(Behaviour):
    use = [CellProximityMechanism]

    def run(self, data):
        around_count = len(data[CellProximityMechanism])
        if around_count == 3:
            return 3
        return False

    def action(self, data):
        new_cell = Cell(
            simulation=self.simulation,
            position=self.subject.position,
        )
        self.simulation.subjects.remove(self.subject)
        self.simulation.subjects.append(new_cell)


class Cell(XYZSubjectMixin, Subject):
    collections = Subject.collections[:]
    collections.extend([COLLECTION_CELL])
    behaviours_classes = [CellDieBehaviour]


class Empty(XYZSubjectMixin, Subject):
    """Represent empty position where cell can spawn"""
    behaviours_classes = [CellBornBehaviour]
