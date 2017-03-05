# coding: utf-8
from random import randint

from sandbox.engulf.const import COLLECTION_GRASS
from synergine2.simulation import SubjectBehaviour, SimulationMechanism, SimulationBehaviour
from synergine2.simulation import Event
from synergine2.utils import ChunkManager
from synergine2.xyz import ProximitySubjectMechanism
from synergine2.xyz_utils import get_around_positions_of_positions, get_around_positions_of


class GrassGrownUp(Event):
    def __init__(self, subject_id, density, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.subject_id = subject_id
        self.density = density

    def repr_debug(self) -> str:
        return '{}: subject_id:{}, density:{}'.format(
            self.__class__.__name__,
            self.subject_id,
            self.density,
        )


class GrassSpawn(Event):
    def __init__(self, subject_id, position, density, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.subject_id = subject_id
        self.position = position
        self.density = density

    def repr_debug(self) -> str:
        return '{}: subject_id:{}, position:{}, density:{}'.format(
            self.__class__.__name__,
            self.subject_id,
            self.position,
            self.density,
        )


class GrassSpotablePositionsMechanism(SimulationMechanism):
    parallelizable = True

    def run(self, process_number: int=None, process_count: int=None):
        chunk_manager = ChunkManager(process_count)
        positions = list(self.simulation.subjects.grass_xyz.keys())
        positions_chunks = chunk_manager.make_chunks(positions)
        spotables = []

        for position in positions_chunks[process_number]:
            arounds = get_around_positions_of_positions(position)
            from_subject = self.simulation.subjects.grass_xyz[position]
            around_data = {
                'from_subject': from_subject,
                'around': [],
            }
            for around in arounds:
                if around not in self.simulation.subjects.grass_xyz:
                    around_data['around'].append(around)

            if around_data['around']:
                spotables.append(around_data)

        return spotables


class GrowUp(SubjectBehaviour):
    frequency = 20

    def run(self, data):
        return True

    def action(self, data) -> [Event]:
        self.subject.density += 1
        return [GrassGrownUp(
            self.subject.id,
            self.subject.density,
        )]


class GrassSpawnBehaviour(SimulationBehaviour):
    frequency = 100
    use = [GrassSpotablePositionsMechanism]

    def run(self, data):
        spawns = []

        for around_data in data[GrassSpotablePositionsMechanism]:
            from_subject = around_data['from_subject']
            arounds = around_data['around']
            if from_subject.density >= 40:
                spawns.extend(arounds)

        return spawns

    @classmethod
    def merge_data(cls, new_data, start_data=None):
        start_data = start_data or []
        start_data.extend(new_data)
        return start_data

    def action(self, data) -> [Event]:
        from sandbox.engulf.subject import Grass  # cyclic
        events = []

        for position in data:
            if position not in list(self.simulation.subjects.grass_xyz.keys()):
                new_grass = Grass(
                    self.simulation,
                    position=position,
                    density=20,
                )
                self.simulation.subjects.append(new_grass)
                events.append(GrassSpawn(
                    new_grass.id,
                    new_grass.position,
                    new_grass.density,
                ))

        return events


class EatableDirectProximityMechanism(ProximitySubjectMechanism):
    distance = 1.41  # distance when on angle
    feel_collections = [COLLECTION_GRASS]


class MoveTo(Event):
    def __init__(self, subject_id: int, position: tuple, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.subject_id = subject_id
        self.position = position

    def repr_debug(self) -> str:
        return '{}: subject_id:{}, position:{}'.format(
            type(self).__name__,
            self.subject_id,
            self.position,
        )


class SearchFood(SubjectBehaviour):
    """
    Si une nourriture a une case de distance et cellule non rassasié, move dans sa direction.
    """
    use = [EatableDirectProximityMechanism]

    def run(self, data):
        pass


class Eat(SubjectBehaviour):
    """
    Prduit un immobilisme si sur une case de nourriture, dans le cas ou la cellule n'est as rassasié.
    """
    def run(self, data):
        pass


class Explore(SubjectBehaviour):
    """
    Produit un mouvement au hasard (ou un immobilisme)
    """
    use = []

    def action(self, data) -> [Event]:
        position = self.get_random_around_position()
        return [MoveTo(self.subject.id, position)]

    def run(self, data):
        return True  # for now, want move every time

    def get_random_around_position(self):
        around_positions = get_around_positions_of(self.subject.position)
        return around_positions[randint(0, len(around_positions)-1)]
