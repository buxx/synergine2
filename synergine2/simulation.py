# coding: utf-8
import collections
import typing

from synergine2.base import BaseObject
from synergine2.config import Config
from synergine2.share import shared
from synergine2.utils import get_mechanisms_classes


class Intention(object):
    pass


class IntentionManager(object):
    def __init__(self) -> None:
        self.intentions = {}  # type: typing.Dict[typing.Type[Intention], Intention]

    def set(self, intention: Intention) -> None:
        self.intentions[type(intention)] = intention

    def get(self, intention_type: typing.Type[Intention]) -> Intention:
        return self.intentions[intention_type]


class Subject(BaseObject):
    collections = []
    behaviours_classes = []
    behaviour_selector_class = None  # type: typing.Type[SubjectBehaviourSelector]
    intention_manager_class = None  # type: typing.Type[IntentionManager]

    def __init__(
        self,
        config: Config,
        simulation: 'Simulation',
    ):
        # TODO: Bannir les attribut de classe passé en reference ! Et meme virer les attr de classe tout court.
        self.collections = self.collections[:]

        self.config = config
        self._id = id(self)  # We store object id because it's lost between process
        self.simulation = simulation
        self.intentions = None

        if self.behaviour_selector_class:
            self.behaviour_selector = self.behaviour_selector_class()
        else:
            self.behaviour_selector = SubjectBehaviourSelector()

        if self.intention_manager_class:
            self.intentions = self.intention_manager_class()
        else:
            self.intentions = IntentionManager()

    @property
    def id(self) -> int:
        try:
            return self._id
        except AttributeError:
            pass

    def change_id(self, id_: int) -> None:
        self._id = id_

    def expose(self) -> None:
        subject_behaviours_index = shared.get('subject_behaviours_index').setdefault(self._id, [])
        subject_mechanisms_index = shared.get('subject_mechanisms_index').setdefault(self._id, [])
        subject_classes = shared.get('subject_classes')

        for behaviour_class in self.behaviours_classes:
            subject_behaviours_index.append(id(behaviour_class))
            for mechanism_class in behaviour_class.use:
                subject_mechanisms_index.append(id(mechanism_class))

        subject_classes[self._id] = id(type(self))

        for collection in self.collections:
            self.simulation.collections.setdefault(collection, []).append(self.id)

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
        # Remove from collections
        for collection_name in value.collections:
            self.simulation.collections[collection_name].remove(value)
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
    behaviours_classes = []

    subject_behaviours_index = shared.create('subject_behaviours_index', {})
    subject_mechanisms_index = shared.create('subject_mechanisms_index', {})
    subject_classes = shared.create('subject_classes', {})
    collections = shared.create('collections', {})

    def __init__(
        self,
        config: Config,
    ):
        self.config = config
        self._subjects = None  # type: Subjects

        # Should contain all usable class of Behaviors, Mechanisms, SubjectBehaviourSelectors,
        # IntentionManagers, Subject
        self._index = {}  # type: typing.Dict[int, type]
        self._index_locked = False

        self.behaviours = {}
        self.mechanisms = {}

        for mechanism_class in get_mechanisms_classes(self):
            self.mechanisms[mechanism_class.__name__] = mechanism_class(
                config=self.config,
                simulation=self,
            )

        for behaviour_class in self.behaviours_classes:
            self.behaviours[behaviour_class.__name__] = behaviour_class(
                config=self.config,
                simulation=self,
            )

    def add_to_index(self, *classes: type) -> None:
        assert not self._index_locked
        for class_ in classes:
            self._index[id(class_)] = class_

    @property
    def index(self) -> typing.Dict[int, type]:
        return self._index

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
            subject_class_id = shared.get('subject_classes')[subject_id]
            subject_class = self.index[subject_class_id]
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

    def run(self):
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

    def run(self, process_id: int=None, process_count: int=None):
        raise NotImplementedError()


class Event(BaseObject):
    def __init__(self, *args, **kwargs):
        pass

    def repr_debug(self) -> str:
        return self.__class__.__name__


class Behaviour(BaseObject):
    def run(self, data):
        raise NotImplementedError()


class SubjectBehaviour(Behaviour):
    frequency = 1
    use = []  # type: typing.List[typing.Type[SubjectMechanism]]

    def __init__(
            self,
            config: Config,
            simulation: Simulation,
            subject: Subject,
    ):
        self.config = config
        self.simulation = simulation
        self.subject = subject

    def run(self, data):
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
    frequency = 1
    use = []

    def __init__(
            self,
            config: Config,
            simulation: Simulation,
    ):
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
