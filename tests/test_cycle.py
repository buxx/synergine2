# coding: utf-8
from synergine2.config import Config
from synergine2.cycle import CycleManager
from synergine2.log import SynergineLogger
from synergine2.share import shared
from synergine2.simulation import Simulation
from synergine2.simulation import SimulationBehaviour
from synergine2.simulation import SimulationMechanism
from synergine2.simulation import Event
from synergine2.simulation import Subject
from synergine2.simulation import Subjects
from synergine2.simulation import SubjectMechanism
from synergine2.simulation import SubjectBehaviour
from tests import BaseTest


class MyEvent(Event):
    def __init__(self, value):
        self.value = value


class MySubjectMechanism(SubjectMechanism):
    def run(self):
        return 42


class MySubjectBehavior(SubjectBehaviour):
    use = [MySubjectMechanism]

    def run(self, data):
        class_name = MySubjectMechanism.__name__
        if class_name in data and data[class_name] == 42:
            return self.subject.id

    def action(self, data) -> [Event]:
        return [MyEvent(data * 2)]


class MySubject(Subject):
    behaviours_classes = [MySubjectBehavior]


class MySubjects(Subjects):
    pass


class MySimulationMechanism(SimulationMechanism):
    def run(self, process_number: int = None, process_count: int = None):
        return process_number + 1000


class MySimulationBehaviour(SimulationBehaviour):
    use = [MySimulationMechanism]

    @classmethod
    def merge_data(cls, new_data, start_data=None):
        start_data = start_data or 0
        return start_data + new_data

    def run(self, data):
        return data['MySimulationMechanism'] * 2

    def action(self, data) -> [Event]:
        return [MyEvent(data)]


class MySimulation(Simulation):
    behaviours_classes = [MySimulationBehaviour]


class TestCycle(BaseTest):
    def test_subjects_cycle(self):
        shared.reset()
        config = Config({'core': {'use_x_cores': 2}})
        logger = SynergineLogger(name='test')

        simulation = Simulation(config)
        subjects = MySubjects(simulation=simulation)
        simulation.subjects = subjects

        # Prepare simulation class index
        simulation.add_to_index(MySubjectBehavior)
        simulation.add_to_index(MySubjectMechanism)
        simulation.add_to_index(MySubject)

        for i in range(3):
            subjects.append(MySubject(config, simulation=simulation))

        cycle_manager = CycleManager(
            config=config,
            logger=logger,
            simulation=simulation,
        )

        events = cycle_manager.next()
        cycle_manager.stop()

        assert 3 == len(events)
        event_values = [e.value for e in events]
        assert all([s.id * 2 in event_values for s in subjects])

    def test_new_subject(self):
        shared.reset()
        config = Config({'core': {'use_x_cores': 1}})
        logger = SynergineLogger(name='test')

        simulation = Simulation(config)
        subjects = MySubjects(simulation=simulation)
        simulation.subjects = subjects

        # Prepare simulation class index
        simulation.add_to_index(MySubjectBehavior)
        simulation.add_to_index(MySubjectMechanism)
        simulation.add_to_index(MySubject)

        for i in range(3):
            subjects.append(MySubject(config, simulation=simulation))

        cycle_manager = CycleManager(
            config=config,
            logger=logger,
            simulation=simulation,
        )

        events = cycle_manager.next()

        assert 3 == len(events)
        event_values = [e.value for e in events]
        assert all([s.id * 2 in event_values for s in subjects])

        subjects.append(MySubject(config, simulation=simulation))
        events = cycle_manager.next()
        cycle_manager.stop()

        assert 4 == len(events)
        event_values = [e.value for e in events]
        assert all([s.id * 2 in event_values for s in subjects])

    def test_simulation_events(self):
        shared.reset()
        config = Config({'core': {'use_x_cores': 2}})
        logger = SynergineLogger(name='test')

        simulation = MySimulation(config)

        # Prepare simulation class index
        simulation.add_to_index(MySimulationBehaviour, MySimulationMechanism)

        subjects = MySubjects(simulation=simulation)
        simulation.subjects = subjects

        cycle_manager = CycleManager(
            config=config,
            logger=logger,
            simulation=simulation,
        )

        events = cycle_manager.next()
        cycle_manager.stop()

        assert 1 == len(events)
        assert events[0].value == 4002
