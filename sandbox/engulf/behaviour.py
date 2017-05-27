# coding: utf-8
import typing
from random import choice

from sandbox.engulf.const import COLLECTION_GRASS, COLLECTION_CELL, COLLECTION_ALIVE, COLLECTION_PREY
from sandbox.engulf.exceptions import NotFoundWhereToGo
from synergine2.simulation import SubjectBehaviour, SimulationMechanism, SimulationBehaviour, SubjectBehaviourSelector
from synergine2.simulation import Event
from synergine2.utils import ChunkManager
from synergine2.xyz import ProximitySubjectMechanism, DIRECTIONS, DIRECTION_SLIGHTLY, get_direction_from_north_degree
from synergine2.xyz_utils import get_around_positions_of_positions, get_position_for_direction

# Import for typing hint
if False:
    from sandbox.engulf.subject import Grass
    from sandbox.engulf.subject import PreyCell


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
            from_subject = self.simulation.subjects.grass_xyz[position][0]
            around_data = {
                'from_subject': from_subject,
                'around': [],
            }
            for around in arounds:
                if around not in self.simulation.subjects.grass_xyz and self.simulation.is_possible_position(around):
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
                    config=self.config,
                    simulation=self.simulation,
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


class GrassEatableDirectProximityMechanism(ProximitySubjectMechanism):
    distance = 1.41  # distance when on angle
    feel_collections = [COLLECTION_GRASS]

    def acceptable_subject(self, subject: 'Grass') -> bool:
        return subject.density >= self.config.simulation.eat_grass_required_density


class PreyEatableDirectProximityMechanism(ProximitySubjectMechanism):
    distance = 1.41  # distance when on angle
    feel_collections = [COLLECTION_CELL]

    def acceptable_subject(self, subject: 'PreyCell') -> bool:
        # TODO: N'attaquer que des "herbivores" ?
        from sandbox.engulf.subject import PreyCell  # cyclic
        return isinstance(subject, PreyCell)


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


class EatEvent(Event):
    def __init__(self, eaten_id: int, eater_id: int, eaten_new_density: float, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.eaten_id = eaten_id
        self.eater_id = eater_id
        self.eaten_new_density = eaten_new_density


class EatenEvent(Event):
    def __init__(self, eaten_id: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.eaten_id = eaten_id


class AttackEvent(Event):
    def __init__(self, attacker_id: int, attacked_id: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.attacker_id = attacker_id
        self.attacked_id = attacked_id


class SearchFood(SubjectBehaviour):
    mechanism_data_class = NotImplemented

    def get_required_appetite(self) -> float:
        raise NotImplementedError()

    def run(self, data):
        if self.subject.appetite < self.get_required_appetite():
            return False

        if not data[self.mechanism_data_class]:
            return False

        direction_degrees = [d['direction'] for d in data[self.mechanism_data_class]]
        return get_direction_from_north_degree(choice(direction_degrees))

    def action(self, data) -> [Event]:
        direction = data
        position = get_position_for_direction(self.subject.position, direction)
        self.subject.position = position
        self.subject.previous_direction = direction

        return [MoveTo(self.subject.id, position)]


class SearchGrass(SearchFood):
    """
    Si une nourriture a une case de distance et cellule non rassasié, move dans sa direction.
    """
    use = [GrassEatableDirectProximityMechanism]
    mechanism_data_class = use[0]

    def get_required_appetite(self) -> float:
        return self.config.simulation.search_food_appetite_required


class SearchPrey(SearchFood):
    """
    Si une nourriture a une case de distance et cellule non rassasié, move dans sa direction.
    """
    use = [PreyEatableDirectProximityMechanism]
    mechanism_data_class = use[0]

    def get_required_appetite(self) -> float:
        return self.config.simulation.search_and_attack_prey_apetite_required


class EatGrass(SubjectBehaviour):
    def run(self, data):
        if self.subject.appetite < self.config.simulation.eat_grass_required_density:
            return False

        for grass in self.simulation.collections.get(COLLECTION_GRASS, []):
            # TODO: Use simulation/xyz pre calculated indexes
            if grass.position == self.subject.position:
                return grass.id

    def action(self, data) -> [Event]:
        subject_id = data

        grass = self.simulation.subjects.index[subject_id]  # TODO: cas ou grass disparu ?
        grass.density -= self.config.simulation.eat_grass_density_reduction

        self.subject.appetite -= self.config.simulation.eat_grass_appetite_reduction

        # TODO: Comment mettre des logs (ne peuvent pas être passé aux subprocess)?

        return [EatEvent(
            eater_id=self.subject.id,
            eaten_id=subject_id,
            eaten_new_density=grass.density,
        )]


class EatPrey(SubjectBehaviour):
    def run(self, data):
        if self.subject.appetite < self.config.simulation.search_and_attack_prey_apetite_required:
            return False

        for prey in self.simulation.collections.get(COLLECTION_PREY, []):
            # TODO: Use simulation/xyz pre calculated indexes
            if prey.position == self.subject.position:
                return prey.id

    def action(self, data) -> [Event]:
        subject_id = data

        # Cell already eaten ?
        if subject_id not in self.simulation.subjects.index:
            return []

        prey = self.simulation.subjects.index[subject_id]
        self.simulation.subjects.remove(prey)
        self.subject.appetite -= self.config.simulation.eat_prey_required_density

        return [EatenEvent(
            eaten_id=prey.id,
        )]


class Explore(SubjectBehaviour):
    """
    Produit un mouvement au hasard (ou un immobilisme)
    """
    use = []

    def run(self, data):
        # TODO: Il faut pouvoir dire tel behaviour concerne que tel collections
        if COLLECTION_ALIVE not in self.subject.collections:
            return False

        return True

    def action(self, data) -> [Event]:
        try:
            position, direction = self.get_random_position_and_direction()
            self.subject.position = position
            self.subject.previous_direction = direction
            return [MoveTo(self.subject.id, position)]
        except NotFoundWhereToGo:
            return []

    def get_random_position_and_direction(self) -> tuple:
        attempts = 0

        while attempts <= 5:
            attempts += 1
            direction = self.get_random_direction()
            position = get_position_for_direction(self.subject.position, direction)

            if self.simulation.is_possible_subject_position(self.subject, position):
                return position, direction

            # If blocked, permit any direction (not slightly)
            if attempts >= 3:
                self.subject.previous_direction = None

        raise NotFoundWhereToGo()

    def get_random_direction(self):
        if not self.subject.previous_direction:
            return choice(DIRECTIONS)
        return choice(DIRECTION_SLIGHTLY[self.subject.previous_direction])


class Hungry(SubjectBehaviour):
    def run(self, data):
        return True

    def action(self, data) -> [Event]:
        self.subject.appetite += self.config.simulation.hungry_reduction
        return []

    def get_random_direction(self):
        if not self.subject.previous_direction:
            return choice(DIRECTIONS)
        return choice(DIRECTION_SLIGHTLY[self.subject.previous_direction])


class Attack(SubjectBehaviour):
    use = [PreyEatableDirectProximityMechanism]

    def run(self, data):
        if self.subject.appetite < self.config.simulation.search_and_attack_prey_apetite_required:
            return False

        eatable_datas = data[PreyEatableDirectProximityMechanism]
        attackable_datas = []

        for eatable_data in eatable_datas:
            if COLLECTION_ALIVE in eatable_data['subject'].collections:
                attackable_datas.append(eatable_data)

        if attackable_datas:
            return choice(attackable_datas)
        return False

    def action(self, data) -> [Event]:
        attacked = self.simulation.subjects.index[data['subject'].id]

        try:
            # TODO il faut automatiser/Refactoriser le fait de retirer/ajouter un collection
            self.simulation.collections[COLLECTION_ALIVE].remove(attacked)
            attacked.collections.remove(COLLECTION_ALIVE)
        except ValueError:
            pass  # On considere qu'il a ete tué par une autre, TODO: en être sur ?

        return [AttackEvent(attacker_id=self.subject.id, attacked_id=data['subject'].id)]


class CellBehaviourSelector(SubjectBehaviourSelector):
    # If behaviour in sublist, only one be kept in sublist
    behaviour_hierarchy = (  # TODO: refact it
        (
            EatPrey,
            EatGrass,  # TODO: Introduce priority with appetite
            Attack,
            SearchPrey,
            SearchGrass,  # TODO: Introduce priority with appetite
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
                    if position is None or behaviour_position < position:
                        position = behaviour_position
                except ValueError:
                    pass

        return position
