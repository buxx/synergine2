import collections

from synergine2.utils import get_mechanisms_classes


class Subject(object):
    collections = []
    behaviours_classes = []

    def __init__(self, simulation: 'Simulation'):
        self.id = id(self)  # We store object id because it's lost between process
        self.simulation = simulation
        self.behaviours = {}
        self.mechanisms = {}

        for collection in self.collections:
            self.simulation.collections[collection].append(self)

        self.initialize()

    def initialize(self):
        for mechanism_class in get_mechanisms_classes(self):
            self.mechanisms[mechanism_class] = mechanism_class(
                simulation=self.simulation,
                subject=self,
            )

        for behaviour_class in self.behaviours_classes:
            self.behaviours[behaviour_class] = behaviour_class(
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

    def __init__(self):
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
                simulation=self,
            )

        for behaviour_class in self.behaviours_classes:
            self.behaviours[behaviour_class] = behaviour_class(
                simulation=self,
            )


class SubjectMechanism(object):
    def __init__(
            self,
            simulation: Simulation,
            subject: Subject,
    ):
        self.simulation = simulation
        self.subject = subject

    def run(self):
        raise NotImplementedError()


class SimulationMechanism(object):
    """If parallelizable behaviour, call """
    parallelizable = False

    def __init__(
            self,
            simulation: Simulation,
    ):
        self.simulation = simulation

    def run(self, process_id: int=None, process_count: int=None):
        raise NotImplementedError()


class Event(object):
    def __init__(self, *args, **kwargs):
        pass


class SubjectBehaviour(object):
    def __init__(
            self,
            simulation: Simulation,
            subject: Subject,
    ):
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
        raise NotImplementedError()

    def action(self, data) -> [Event]:
        """
        Method called in main process
        Return events will be give to terminals
        """
        raise NotImplementedError()


class SimulationBehaviour(object):
    def __init__(
            self,
            simulation: Simulation,
    ):
        self.simulation = simulation

    def run(self, data):
        """
        Method called in subprocess if mechanisms are
        parallelizable, in main process if not.
        """
        raise NotImplementedError()

    def action(self, data) -> [Event]:
        """
        Method called in main process
        Return events will be give to terminals
        """
        raise NotImplementedError()
