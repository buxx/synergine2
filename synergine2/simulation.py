import collections

from synergine2.utils import initialize_subject


class Simulation(object):
    def __init__(self):
        self.collections = collections.defaultdict(list)
        self._subjects = None

    @property
    def subjects(self):
        return self._subjects

    @subjects.setter
    def subjects(self, value: 'Subjects'):
        if not isinstance(value, Subjects):
            raise Exception('Simulation.subjects must be Subjects type')
        self._subjects = value


class Subject(object):
    collections = []
    behaviours_classes = []

    def __init__(self, simulation: Simulation):
        self.id = id(self)  # We store object id because it's lost between process
        self.simulation = simulation
        self.behaviours = {}
        self.mechanisms = {}

        for collection in self.collections:
            self.simulation.collections[collection].append(self)

        initialize_subject(
            simulation=simulation,
            subject=self,
        )


class Subjects(list):
    def __init__(self, *args, **kwargs):
        self.simulation = kwargs.pop('simulation')
        super().__init__(*args, **kwargs)

    def remove(self, value: Subject):
        super().remove(value)
        for collection_name in value.collections:
            self.simulation.collections[collection_name].remove(value)


class Mechanism(object):
    def __init__(
            self,
            simulation: Simulation,
            subject: Subject,
    ):
        self.simulation = simulation
        self.subject = subject

    def run(self):
        raise NotImplementedError()


class Behaviour(object):
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

    def action(self, data) -> object:
        """
        Method called in main process
        Return value will be give to terminals
        """
        raise NotImplementedError()
