# coding: utf-8
import typing

import time

from synergine2.base import BaseObject
from synergine2.base import IdentifiedObject
from synergine2.config import Config
from synergine2.exceptions import ConfigurationError
from synergine2.share import shared
from synergine2.utils import get_mechanisms_classes


class Intention(object):
    pass


class IntentionManager(object):
    intentions = shared.create_self('intentions', lambda: {})  # type: typing.Dict[typing.Type[Intention], Intention]

    def __init__(self):
        self._id = id(self)

    @property
    def id(self) -> int:
        return self._id

    def set(self, intention: Intention) -> None:
        self.intentions[type(intention)] = intention

    def get(self, intention_type: typing.Type[Intention]) -> Intention:
        # TODO: Raise specialised exception if KeyError
        return self.intentions[intention_type]

    def remove(self, intention_type: typing.Type[Intention]) -> None:
        intentions = self.intentions
        del self.intentions[intention_type]
        self.intentions = intentions

    def remove_all(self) -> None:
        self.intentions = {}


class Subject(IdentifiedObject):
    start_collections = []
    behaviours_classes = []
    behaviour_selector_class = None  # type: typing.Type[SubjectBehaviourSelector]
    intention_manager_class = None  # type: typing.Type[IntentionManager]
    collections = shared.create_self('collections', lambda: [])

    def __init__(
        self,
        config: Config,
        simulation: 'Simulation',
        properties: dict=None,
    ):
        """

        :param config: config object
        :param simulation: simulation object
        :param properties: additional data (will not change during simulation)
        """
        super().__init__()
        # FIXME: use shared data to permit dynamic start_collections
        self.collections.extend(self.start_collections[:])

        self.config = config
        self._id = id(self)  # We store object id because it's lost between process
        self.simulation = simulation
        self.intentions = None
        self.properties = properties or {}

        if self.behaviour_selector_class:
            self.behaviour_selector = self.behaviour_selector_class()
        else:
            self.behaviour_selector = SubjectBehaviourSelector()

        if self.intention_manager_class:
            self.intentions = self.intention_manager_class()
        else:
            self.intentions = IntentionManager()

        self._mechanisms = None  # type: typing.Dict[typing.Type['SubjectMechanism'], 'SubjectMechanism']
        self._behaviours = None  # type: typing.Dict[typing.Type['SubjectBehaviour'], 'SubjectBehaviour']

    @property
    def mechanisms(self) -> typing.Dict[typing.Type['SubjectMechanism'], 'SubjectMechanism']:
        if self._mechanisms is None:
            self._mechanisms = {}
            for behaviour_class in self.behaviours_classes:
                for mechanism_class in behaviour_class.use:
                    mechanism = mechanism_class(
                        self.config,
                        self.simulation,
                        self,
                    )
                    self._mechanisms[mechanism_class] = mechanism
        return self._mechanisms

    @property
    def behaviours(self) -> typing.Dict[typing.Type['SubjectBehaviour'], 'SubjectBehaviour']:
        if self._behaviours is None:
            self._behaviours = {}
            for behaviour_class in self.behaviours_classes:
                behaviour = behaviour_class(
                    self.config,
                    self.simulation,
                    self,
                )
                self._behaviours[behaviour_class] = behaviour
        return self._behaviours

    def change_id(self, id_: int) -> None:
        self._id = id_

    def expose(self) -> None:
        subject_classes = shared.get('subject_classes')
        subject_classes[self._id] = type(self)
        shared.set('subject_classes', subject_classes)

        for collection in self.collections:
            self.simulation.collections.setdefault(collection, []).append(self.id)

    def remove_collection(self, collection_name: str) -> None:
        self.collections.remove(collection_name)
        # Manipulate as shared property
        simulation_collection = self.simulation.collections[collection_name]
        simulation_collection.remove(self.id)
        self.simulation.collections[collection_name] = simulation_collection

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return '{}({})'.format(
            type(self).__name__,
            self.id,
        )


class Subjects(list):
    """
    TODO: Manage other list methods
    """
    subject_ids = shared.create('subject_ids', [])

    def __init__(self, *args, **kwargs):
        self.simulation = kwargs.pop('simulation')
        self.removes = []
        self.adds = []
        self.track_changes = False
        self.index = {}
        self._auto_expose = True
        super().__init__(*args, **kwargs)

        if self.auto_expose:
            for subject in self:
                subject.expose()

    @property
    def auto_expose(self) -> bool:
        return self._auto_expose

    @auto_expose.setter
    def auto_expose(self, value: bool) -> None:
        assert self._auto_expose
        self._auto_expose = value

    def remove(self, value: Subject):
        # Remove from index
        del self.index[value.id]
        self.subject_ids.remove(value.id)
        # Remove from subjects list
        super().remove(value)
        # Remove from start_collections
        for collection_name in value.collections:
            self.simulation.collections[collection_name].remove(value.id)
        # Add to removed listing
        if self.track_changes:
            self.removes.append(value)
        # TODO: Supprimer des choses du shared ! Sinon fuite mémoire dans la bdd

    def append(self, p_object):
        # Add to index
        self.index[p_object.id] = p_object
        self.subject_ids.append(p_object.id)
        # Add to subjects list
        super().append(p_object)
        # Add to adds list
        if self.track_changes:
            self.adds.append(p_object)
        if self.auto_expose:
            p_object.expose()

    def extend(self, iterable):
        for item in iterable:
            self.append(item)


class Simulation(BaseObject):
    accepted_subject_class = Subjects
    behaviours_classes = []  # type: typing.List[typing.Type[SimulationBehaviour]]

    subject_classes = shared.create('subject_classes', {})
    collections = shared.create('collections', {})

    def __init__(
        self,
        config: Config,
    ):
        self.config = config
        self._subjects = None  # type: Subjects

        self._index_locked = False

        self.behaviours = {}
        self.mechanisms = {}

        for mechanism_class in get_mechanisms_classes(self):
            self.mechanisms[mechanism_class] = mechanism_class(
                config=self.config,
                simulation=self,
            )

        for behaviour_class in self.behaviours_classes:
            self.behaviours[behaviour_class] = behaviour_class(
                config=self.config,
                simulation=self,
            )

    def lock_index(self) -> None:
        self._index_locked = True

    @property
    def subjects(self):
        return self._subjects

    @subjects.setter
    def subjects(self, value: 'Subjects'):
        if not isinstance(value, self.accepted_subject_class):
            raise Exception('Simulation.subjects must be {0} type'.format(
                self.accepted_subject_class,
            ))
        self._subjects = value

    def get_or_create_subject(self, subject_id: int) -> Subject:
        try:
            return self._subjects.index[subject_id]
        except KeyError:
            # We should be in process context and subject have to been created
            subject_class = shared.get('subject_classes')[subject_id]
            subject = subject_class(self.config, self)
            subject.change_id(subject_id)
            self.subjects.append(subject)
            return subject


class Mechanism(BaseObject):
    pass


class SubjectMechanism(Mechanism):
    def __init__(
            self,
            config: Config,
            simulation: Simulation,
            subject: Subject,
    ):
        self.config = config
        self.simulation = simulation
        self.subject = subject

    def run(self) -> dict:
        raise NotImplementedError()


class SimulationMechanism(Mechanism):
    """If parallelizable behaviour, call """
    parallelizable = False

    def __init__(
            self,
            config: Config,
            simulation: Simulation,
    ):
        self.config = config
        self.simulation = simulation

    def repr_debug(self) -> str:
        return self.__class__.__name__

    def run(self, process_number: int=None, process_count: int=None):
        raise NotImplementedError()


class Event(BaseObject):
    def repr_debug(self) -> str:
        return self.__class__.__name__


class Behaviour(BaseObject):
    def __init__(self):
        self.last_execution_time = 0

    @property
    def cycle_frequency(self) -> typing.Optional[float]:
        return None

    @property
    def seconds_frequency(self) -> typing.Optional[float]:
        """
        If this behaviour is time based, return here the waiting time between two
        executions. IMPORTANT: your behaviour have to update it's
        self.last_execution_time attribute when executed (in `run` method)!
        :return: float number of period in seconds
        """
        return None

    def run(self, data):
        raise NotImplementedError()

    def is_skip(self, cycle_number: int) -> bool:
        """
        :return: True if behaviour have to be skip this time
        """
        cycle_frequency = self.cycle_frequency
        if cycle_frequency is not None:
            return bool(cycle_number % cycle_frequency)

        seconds_frequency = self.seconds_frequency
        if seconds_frequency is not None:
            return float(time.time() - self.last_execution_time) <= seconds_frequency

        return False


class SubjectBehaviour(Behaviour):
    use = []  # type: typing.List[typing.Type[SubjectMechanism]]

    def __init__(
            self,
            config: Config,
            simulation: Simulation,
            subject: Subject,
    ):
        super().__init__()
        self.config = config
        self.simulation = simulation
        self.subject = subject

    def is_terminated(self) -> bool:
        """
        :return: True if behaviour will no longer exist (can be removed from simulation)
        """
        return False

    def run(self, data) -> object:
        """
        Method called in subprocess.
        If return equivalent to False, behaviour produce nothing.
        If return equivalent to True, action bahaviour method
        will be called with these data
        Note: Returned data will be transfered from sub processes.
              Prefer scalar types.
        """
        raise NotImplementedError()  # TODO Test it and change to strictly False

    def action(self, data) -> [Event]:
        """
        Method called in main process
        Return events will be give to terminals
        """
        raise NotImplementedError()


class SimulationBehaviour(Behaviour):
    use = []  # type: typing.List[typing.Type[SimulationMechanism]]

    def __init__(
            self,
            config: Config,
            simulation: Simulation,
    ):
        super().__init__()
        self.config = config
        self.simulation = simulation

    def run(self, data):
        """
        Method called in subprocess if mechanisms are
        parallelizable, in main process if not.
        """
        raise NotImplementedError()

    @classmethod
    def merge_data(cls, new_data, start_data=None):
        """
        Called if behaviour executed in subprocess
        """
        raise NotImplementedError()

    def action(self, data) -> [Event]:
        """
        Method called in main process
        Return events will be give to terminals
        """
        raise NotImplementedError()


class SubjectBehaviourSelector(BaseObject):
    def reduce_behaviours(
        self,
        behaviours: typing.Dict[typing.Type[SubjectBehaviour], object],
    ) -> typing.Dict[typing.Type[SubjectBehaviour], object]:
        return behaviours


class BehaviourStep(object):
    def proceed(self) -> 'BehaviourStep':
        raise NotImplementedError()

    def generate_data(self) -> typing.Any:
        raise NotImplementedError()

    def get_events(self) -> typing.List[Event]:
        raise NotImplementedError()


class SubjectComposedBehaviour(SubjectBehaviour):
    """
    SubjectComposedBehaviour receive data in run (and will will it's step with it).
    These data can be the first data of behaviour, or last behaviour subject data
    produced in action.
    SubjectComposedBehaviour produce data in run only if something happen and must be
    given in future run.
    """
    step_classes = None  # type: typing.List[typing.Tuple[typing.Type[BehaviourStep], typing.Callable[[typing.Any], bool]]]  # nopep8

    def __init__(
        self,
        config: Config,
        simulation: Simulation,
        subject: Subject,
    ) -> None:
        super().__init__(config, simulation, subject)
        if self.step_classes is None:
            raise ConfigurationError(
                '{}: you must set step_classes class attribute'.format(
                    self.__class__.__name__,
                ),
            )

    def get_step(self, data) -> BehaviourStep:
        for step_class, step_test_callable in self.step_classes:
            if step_test_callable(data):
                return step_class(**data)

        raise ConfigurationError(
            '{}: No step choose for following data: {}'.format(
                self.__class__.__name__,
                data,
            ),
        )

    def run(self, data):
        step = self.get_step(data)
        next_step = step.proceed()
        return next_step.generate_data()

    def action(self, data):
        step = self.get_step(data)
        return step.get_events()
