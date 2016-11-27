from synergine2.simulation import Subject, SimulationMechanism, Simulation
from synergine2.simulation import SimulationBehaviour
from synergine2.simulation import Event
from synergine2.simulation import SubjectBehaviour
from synergine2.utils import ChunkManager
from synergine2.xyz import ProximitySubjectMechanism, ProximityMixin
from synergine2.xyz import XYZSubjectMixin
from synergine2.xyz_utils import get_around_positions_of_positions, get_min_and_max

COLLECTION_CELL = 'COLLECTION_CELL'  # Collections of Cell type


class CellDieEvent(Event):
    def __init__(self, subject_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.subject_id = subject_id


class CellBornEvent(Event):
    def __init__(self, subject_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.subject_id = subject_id


class EmptyPositionWithLotOfCellAroundEvent(Event):
    def __init__(self, position, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.position = position


class CellProximityMechanism(ProximitySubjectMechanism):
    distance = 1.41  # distance when on angle
    feel_collections = [COLLECTION_CELL]


class CellAroundAnEmptyPositionMechanism(ProximityMixin, SimulationMechanism):
    distance = 1.41  # distance when on angle
    feel_collections = [COLLECTION_CELL]
    parallelizable = True

    def run(self, process_number: int=None, process_count: int=None):
        chunk_manager = ChunkManager(process_count)
        positions = self.simulation.subjects.xyz.keys()
        min_x, max_x, min_y, max_y, min_z, max_z = get_min_and_max(positions)
        xs = list(range(min_x, max_x+1))
        xs_chunks = chunk_manager.make_chunks(xs)

        results = {}
        for z in range(min_z, max_z+1):
            for y in range(min_y, max_y+1):
                for x in xs_chunks[process_number]:
                    subject_here = self.simulation.subjects.xyz.get((x, y, z))
                    if not subject_here or isinstance(subject_here, Empty):
                        subjects = self.get_for_position(
                            position=(x, y, z),
                            simulation=self.simulation,
                        )
                        results[(x, y, z)] = subjects

        return results


class CellDieBehaviour(SubjectBehaviour):
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


class CellBornBehaviour(SubjectBehaviour):
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

        positions_to_complete = get_around_positions_of_positions(self.subject.position)
        for position in positions_to_complete:
            if position not in self.simulation.subjects.xyz:
                new_empty = Empty(
                    simulation=self.simulation,
                    position=position,
                )
                # Ici on casse le SimplePrintTerminal (car on créer des ligne avec des espaces manquants ?)
                self.simulation.subjects.append(new_empty)

        self.simulation.subjects.remove(self.subject)
        self.simulation.subjects.append(new_cell)
        return [CellBornEvent(new_cell.id)]


class InvertCellStateBehaviour(SimulationBehaviour):
    def run(self, data):
        pass  # This behaviour is designed to be launch by terminal

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
        return [CellDieEvent(new_empty)]


class LotOfCellsSignalBehaviour(SimulationBehaviour):
    use = [CellAroundAnEmptyPositionMechanism]

    def run(self, data):
        positions = []

        for position, subjects in data[CellAroundAnEmptyPositionMechanism].items():
            if len(subjects) >= 4:
                positions.append(position)

        return positions

    @classmethod
    def merge_data(cls, new_data, start_data=None):
        start_data = start_data or []
        start_data.extend(new_data)
        return start_data

    def action(self, data) -> [Event]:
        events = []

        for position in data:
            events.append(EmptyPositionWithLotOfCellAroundEvent(position))

        return events


class Cell(XYZSubjectMixin, Subject):
    collections = Subject.collections[:]
    collections.extend([COLLECTION_CELL])
    behaviours_classes = [CellDieBehaviour]


class Empty(XYZSubjectMixin, Subject):
    """Represent empty position where cell can spawn"""
    behaviours_classes = [CellBornBehaviour]


class LifeGame(Simulation):
    behaviours_classes = [LotOfCellsSignalBehaviour]
