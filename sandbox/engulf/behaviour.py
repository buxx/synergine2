# coding: utf-8
import typing
from random import choice

from sandbox.engulf.const import COLLECTION_GRASS
from synergine2.simulation import SubjectBehaviour, SimulationMechanism, SimulationBehaviour, SubjectBehaviourSelector
from synergine2.simulation import Event
from synergine2.utils import ChunkManager
from synergine2.xyz import ProximitySubjectMechanism, DIRECTIONS, DIRECTION_SLIGHTLY, DIRECTION_FROM_NORTH_DEGREES, \
    get_direction_from_north_degree
from synergine2.xyz_utils import get_around_positions_of_positions, get_around_positions_of, get_position_for_direction


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
        if not data[EatableDirectProximityMechanism]:
            return False

        direction_degrees = [d['direction'] for d in data[EatableDirectProximityMechanism]]
        return get_direction_from_north_degree(choice(direction_degrees))

    def action(self, data) -> [Event]:
        direction = data
        position = get_position_for_direction(self.subject.position, direction)
        self.subject.position = position
        self.subject.previous_direction = direction

        return [MoveTo(self.subject.id, position)]


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

    def run(self, data):
        return True  # for now, want move every time

    def action(self, data) -> [Event]:
        direction = self.get_random_direction()
        position = get_position_for_direction(self.subject.position, direction)
        self.subject.position = position
        self.subject.previous_direction = direction

        return [MoveTo(self.subject.id, position)]

    def get_random_direction(self):
        if not self.subject.previous_direction:
            return choice(DIRECTIONS)
        return choice(DIRECTION_SLIGHTLY[self.subject.previous_direction])


class CellBehaviourSelector(SubjectBehaviourSelector):
    # If behaviour in sublist, only one be kept in sublist
    behaviour_hierarchy = (  # TODO: refact it
        (
            Eat,
            SearchFood,
            Explore,
        ),
    )

    def reduce_behaviours(
        self,
        behaviours: typing.Dict[typing.Type[SubjectBehaviour], object],
    ) -> typing.Dict[typing.Type[SubjectBehaviour], object]:
        reduced_behaviours = {}  # type: typing.Dict[typing.Type[SubjectBehaviour], object]

        for behaviour_class, behaviour_data in behaviours.items():
            if not self.behaviour_class_in_sublist(behaviour_class):
                reduced_behaviours[behaviour_class] = behaviour_data
            elif self.behaviour_class_is_prior(behaviour_class, behaviours):
                reduced_behaviours[behaviour_class] = behaviour_data

        return reduced_behaviours

    def behaviour_class_in_sublist(self, behaviour_class: typing.Type[SubjectBehaviour]) -> bool:
        for sublist in self.behaviour_hierarchy:
            if behaviour_class in sublist:
                return True
        return False

    def behaviour_class_is_prior(
        self,
        behaviour_class: typing.Type[SubjectBehaviour],
        behaviours: typing.Dict[typing.Type[SubjectBehaviour], object],
    ) -> bool:
        for sublist in self.behaviour_hierarchy:
            if behaviour_class in sublist:
                behaviour_position = sublist.index(behaviour_class)
                other_behaviour_top_position = self.get_other_behaviour_top_position(
                    behaviour_class,
                    behaviours,
                    sublist,
                )
                if other_behaviour_top_position is not None and behaviour_position > other_behaviour_top_position:
                    return False
        return True

    def get_other_behaviour_top_position(
        self,
        exclude_behaviour_class,
        behaviours,
        sublist,
    ) -> typing.Union[None, int]:
        position = None
        for behaviour_class in behaviours.keys():
            if behaviour_class != exclude_behaviour_class:
                try:
                    behaviour_position = sublist.index(behaviour_class)
                except ValueError:
                    pass
                if position is None or behaviour_position < position:
                    position = behaviour_position

        return position
