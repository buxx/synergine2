# coding: utf-8
from synergine2.simulation import SubjectBehaviour, SimulationMechanism, SimulationBehaviour
from synergine2.simulation import Event
from synergine2.utils import ChunkManager
from synergine2.xyz_utils import get_around_positions_of_positions


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
