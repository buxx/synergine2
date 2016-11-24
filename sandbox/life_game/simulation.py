from synergine2.simulation import Subject
from synergine2.simulation import Event
from synergine2.simulation import Behaviour
from synergine2.xyz import ProximityMechanism
from synergine2.xyz import XYZSubjectMixin

COLLECTION_CELL = 'COLLECTION_CELL'  # Collections of Cell type


class CellDieEvent(Event):
    def __init__(self, subject_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.subject_id = subject_id


class CellBornEvent(Event):
    def __init__(self, subject_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.subject_id = subject_id


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
        return [CellDieEvent(self.subject.id)]


class CellBornBehaviour(Behaviour):
    use = [CellProximityMechanism]

    def run(self, data):
        around_count = len(data[CellProximityMechanism])
        if around_count == 3:
            return 3
        return False

    def action(self, data):
        # TODO: une cell born ? Mettre des deads autour pour permetre l'expension
        new_cell = Cell(
            simulation=self.simulation,
            position=self.subject.position,
        )
        self.simulation.subjects.remove(self.subject)
        self.simulation.subjects.append(new_cell)
        return [CellBornEvent(new_cell.id)]


class InvertCellStateBehaviour(Behaviour):
    # TODO: Bhaviour utilisés comme actions ? différentes ? ou comme ça ? Autre classe ?
    def run(self, data):
        pass

    def action(self, data) -> [Event]:
        position = data['position']
        cell_at_position = self.simulation.subjects.xyz.get(position, None)

        if not cell_at_position or isinstance(cell_at_position, Empty):
            new_cell = Cell(
                simulation=self.simulation,
                position=position,
            )
            if cell_at_position:
                self.simulation.subjects.remove(cell_at_position)
            self.simulation.subjects.append(new_cell)
            return [CellBornEvent(new_cell.id)]

        new_empty = Empty(
            simulation=self.simulation,
            position=position,
        )

        self.simulation.subjects.remove(cell_at_position)
        self.simulation.subjects.append(new_empty)
        return [CellDieEvent(self.subject.id)]


class Cell(XYZSubjectMixin, Subject):
    collections = Subject.collections[:]
    collections.extend([COLLECTION_CELL])
    behaviours_classes = [CellDieBehaviour]


class Empty(XYZSubjectMixin, Subject):
    """Represent empty position where cell can spawn"""
    behaviours_classes = [CellBornBehaviour]
