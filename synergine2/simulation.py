# coding: utf-8
import collections
import typing

from synergine2.base import BaseObject
from synergine2.config import Config
from synergine2.utils import get_mechanisms_classes


class Subject(object):
    collections = []
    behaviours_classes = []
    behaviour_selector_class = None  # type: typing.Type[SubjectBehaviourSelector]

    def __init__(
        self,
        config: Config,
        simulation: 'Simulation',
    ):
        self.config = config
        self.id = id(self)  # We store object id because it's lost between process
        self.simulation = simulation
        self.behaviours = {}
        self.mechanisms = {}
        self.behaviour_selector = None  # type: SubjectBehaviourSelector
        if self.behaviour_selector_class:
            self.behaviour_selector = self.behaviour_selector_class()

        for collection in self.collections:
            self.simulation.collections[collection].append(self)

        self.initialize()

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return '{}({})'.format(
            type(self).__name__,
            self.id,
        )

    def initialize(self):
        for mechanism_class in get_mechanisms_classes(self):
            self.mechanisms[mechanism_class] = mechanism_class(
                config=self.config,
                simulation=self.simulation,
                subject=self,
            )

        for behaviour_class in self.behaviours_classes:
            self.behaviours[behaviour_class] = behaviour_class(
                config=self.config,
                simulation=self.simulation,
                subject=self,
            )


class Subjects(list):
    """
    TODO: Manage other list methods
    """
    def __init__(self, *args, **kwargs):
        self.simulation = kwargs.pop('simulation')
        self.removes = []
        self.adds = []
        self.track_changes = False
        self.index = {}
        super().__init__(*args, **kwargs)

    def remove(self, value: Subject):
        # Remove from index
        del self.index[value.id]
        # Remove from subjects list
        super().remove(value)
        # Remove from collections
        for collection_name in value.collections:
            self.simulation.collections[collection_name].remove(value)
        # Add to removed listing
        if self.track_changes:
            self.removes.append(value)

    def append(self, p_object):
        # Add to index
        self.index[p_object.id] = p_object
        # Add to subjects list
        super().append(p_object)
        # Add to adds list
        if self.track_changes:
            self.adds.append(p_object)


class Simulation(object):
    accepted_subject_class = Subjects
    behaviours_classes = []

    def __init__(
        self,
        config: Config,
    ):
        self.config = config
        self.collections = collections.defaultdict(list)
        self._subjects = None
        self.behaviours = {}
        self.mechanisms = {}

        self.initialize()

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

    def initialize(self):
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


class SubjectMechanism(BaseObject):
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


class SimulationMechanism(BaseObject):
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


class SubjectBehaviour(BaseObject):
    frequency = 1
    use = []

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


class SimulationBehaviour(BaseObject):
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
        raise NotImplementedError()
