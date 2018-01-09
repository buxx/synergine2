import datetime
import time

from synergine2.config import Config
from synergine2.cycle import CycleManager
from synergine2.log import SynergineLogger
from synergine2.processing import ProcessManager
from synergine2.share import shared
from synergine2.simulation import Simulation
from synergine2.simulation import Subjects
from synergine2.simulation import SubjectBehaviour
from synergine2.simulation import SubjectMechanism
from synergine2.simulation import Subject
from synergine2.simulation import SimulationMechanism
from synergine2.simulation import SimulationBehaviour
from tests import BaseTest

from freezegun import freeze_time

config = Config()
logger = SynergineLogger('test')


class MySubjectMechanism(SubjectMechanism):
    def run(self):
        return {'foo': 42}


class MySimulationMechanism(SimulationMechanism):
    def run(self, process_number: int=None, process_count: int=None):
        return {'foo': 42}


class MySubjectBehaviour(SubjectBehaviour):
    use = [MySubjectMechanism]

    def run(self, data):
        return {'bar': data[MySubjectMechanism]['foo'] + 100}


class MySimulationBehaviour(SimulationBehaviour):
    use = [MySimulationMechanism]

    def run(self, data):
        return {'bar': data[MySimulationMechanism]['foo'] + 100}


class MySimulation(Simulation):
    behaviours_classes = [MySimulationBehaviour]


class MyCycledSubjectBehaviour(MySubjectBehaviour):
    @property
    def cycle_frequency(self):
        return 2


class MyCycledSimulationBehaviour(MySimulationBehaviour):
    @property
    def cycle_frequency(self):
        return 2


class MyTimedSubjectBehaviour(MySubjectBehaviour):
    @property
    def seconds_frequency(self):
        return 1.0

    def run(self, data):
        self.last_execution_time = time.time()
        return super().run(data)


class MyTimedSimulationBehaviour(MySimulationBehaviour):
    @property
    def seconds_frequency(self):
        return 1.0

    def run(self, data):
        self.last_execution_time = time.time()
        return super().run(data)


class TestBehaviours(BaseTest):
    def test_subject_behaviour_produce_data(
        self,
        do_nothing_process_manager: ProcessManager,
    ):
        shared.reset()

        class MySubject(Subject):
            behaviours_classes = [MySubjectBehaviour]

        simulation = Simulation(config)
        my_subject = MySubject(config, simulation)
        subjects = Subjects(simulation=simulation)
        subjects.append(my_subject)
        simulation.subjects = subjects

        cycle_manager = CycleManager(
            config,
            logger,
            simulation=simulation,
            process_manager=do_nothing_process_manager,
        )
        results_by_subjects = cycle_manager._job_subjects(worker_id=0, process_count=1)
        assert results_by_subjects
        assert id(my_subject) in results_by_subjects
        assert MySubjectBehaviour in results_by_subjects[id(my_subject)]
        assert 'bar' in results_by_subjects[id(my_subject)][MySubjectBehaviour]
        assert 142 == results_by_subjects[id(my_subject)][MySubjectBehaviour]['bar']

    def test_simulation_behaviour_produce_data(
        self,
        do_nothing_process_manager: ProcessManager,
    ):
        shared.reset()
        simulation = MySimulation(config)
        subjects = Subjects(simulation=simulation)
        simulation.subjects = subjects

        cycle_manager = CycleManager(
            config,
            logger,
            simulation=simulation,
            process_manager=do_nothing_process_manager,
        )
        data = cycle_manager._job_simulation(worker_id=0, process_count=1)
        assert data
        assert MySimulationBehaviour in data
        assert 'bar' in data[MySimulationBehaviour]
        assert 142 == data[MySimulationBehaviour]['bar']

    def test_subject_behaviour_cycle_frequency(
        self,
        do_nothing_process_manager: ProcessManager,
    ):
        shared.reset()

        class MySubject(Subject):
            behaviours_classes = [MyCycledSubjectBehaviour]

        simulation = Simulation(config)
        my_subject = MySubject(config, simulation)
        subjects = Subjects(simulation=simulation)
        subjects.append(my_subject)
        simulation.subjects = subjects

        cycle_manager = CycleManager(
            config,
            logger,
            simulation=simulation,
            process_manager=do_nothing_process_manager,
        )

        # Cycle 0: behaviour IS executed
        cycle_manager.current_cycle = 0
        results_by_subjects = cycle_manager._job_subjects(worker_id=0, process_count=1)
        assert results_by_subjects

        # Cycle 1: behaviour IS NOT executed
        cycle_manager.current_cycle = 1
        results_by_subjects = cycle_manager._job_subjects(worker_id=0, process_count=1)
        assert not results_by_subjects

    def test_subject_behaviour_seconds_frequency(
        self,
        do_nothing_process_manager: ProcessManager,
    ):
        shared.reset()

        class MySubject(Subject):
            behaviours_classes = [MyTimedSubjectBehaviour]

        simulation = Simulation(config)
        my_subject = MySubject(config, simulation)
        subjects = Subjects(simulation=simulation)
        subjects.append(my_subject)
        simulation.subjects = subjects

        cycle_manager = CycleManager(
            config,
            logger,
            simulation=simulation,
            process_manager=do_nothing_process_manager,
        )

        # Thirst time, behaviour IS executed
        with freeze_time(datetime.datetime(2000, 12, 1, 0, 0, 0)):
            data = cycle_manager._job_subjects(worker_id=0, process_count=1)
            assert data
            assert id(my_subject) in data
            assert data[id(my_subject)]

        # Less second after: NOT executed
        with freeze_time(datetime.datetime(2000, 12, 1, 0, 0, 0, 500000)):
            data = cycle_manager._job_subjects(worker_id=0, process_count=1)
            assert not data

        # Less second after: NOT executed
        with freeze_time(datetime.datetime(2000, 12, 1, 0, 0, 0, 700000)):
            data = cycle_manager._job_subjects(worker_id=0, process_count=1)
            assert not data

        # Less second after: IS executed
        with freeze_time(datetime.datetime(2000, 12, 1, 0, 0, 1, 500000)):
            data = cycle_manager._job_subjects(worker_id=0, process_count=1)
            assert data

    def test_simulation_behaviour_cycle_frequency(
        self,
        do_nothing_process_manager: ProcessManager,
    ):
        shared.reset()

        class MyCycledSimulation(Simulation):
            behaviours_classes = [MyCycledSimulationBehaviour]

        simulation = MyCycledSimulation(config)
        subjects = Subjects(simulation=simulation)
        simulation.subjects = subjects

        cycle_manager = CycleManager(
            config,
            logger,
            simulation=simulation,
            process_manager=do_nothing_process_manager,
        )

        # Cycle 0: behaviour IS executed
        cycle_manager.current_cycle = 0
        data = cycle_manager._job_simulation(worker_id=0, process_count=1)
        assert data

        # Cycle 1: behaviour IS NOT executed
        cycle_manager.current_cycle = 1
        data = cycle_manager._job_simulation(worker_id=0, process_count=1)
        assert not data

    def test_simulation_behaviour_seconds_frequency(
        self,
        do_nothing_process_manager: ProcessManager,
    ):
        shared.reset()

        class MyTimedSimulation(Simulation):
            behaviours_classes = [MyTimedSimulationBehaviour]

        simulation = MyTimedSimulation(config)
        subjects = Subjects(simulation=simulation)
        simulation.subjects = subjects

        cycle_manager = CycleManager(
            config,
            logger,
            simulation=simulation,
            process_manager=do_nothing_process_manager,
        )

        # Thirst time, behaviour IS executed
        with freeze_time(datetime.datetime(2000, 12, 1, 0, 0, 0)):
            data = cycle_manager._job_simulation(worker_id=0, process_count=1)
            assert data

        # Less second after: NOT executed
        with freeze_time(datetime.datetime(2000, 12, 1, 0, 0, 0, 500000)):
            data = cycle_manager._job_simulation(worker_id=0, process_count=1)
            assert not data

        # Less second after: NOT executed
        with freeze_time(datetime.datetime(2000, 12, 1, 0, 0, 0, 700000)):
            data = cycle_manager._job_simulation(worker_id=0, process_count=1)
            assert not data

        # More second after: IS executed
        with freeze_time(datetime.datetime(2000, 12, 1, 0, 0, 1, 500000)):
            data = cycle_manager._job_simulation(worker_id=0, process_count=1)
            assert data

    def test_subject_behavior_not_called_if_no_more_subjects(
        self,
        do_nothing_process_manager: ProcessManager,
    ):
        shared.reset()

        class MySubject(Subject):
            behaviours_classes = [MySubjectBehaviour]

        simulation = Simulation(config)
        my_subject = MySubject(config, simulation)
        subjects = Subjects(simulation=simulation)
        subjects.append(my_subject)
        simulation.subjects = subjects

        cycle_manager = CycleManager(
            config,
            logger,
            simulation=simulation,
            process_manager=do_nothing_process_manager,
        )
        results_by_subjects = cycle_manager._job_subjects(worker_id=0, process_count=1)
        assert results_by_subjects
        assert id(my_subject) in results_by_subjects
        assert results_by_subjects[id(my_subject)]

        # If we remove subject, no more data generated
        subjects.remove(my_subject)
        results_by_subjects = cycle_manager._job_subjects(worker_id=0, process_count=1)
        assert not results_by_subjects


class TestMechanisms(BaseTest):
    def test_mechanism_called_once_for_multiple_subject_behaviors(
        self,
        do_nothing_process_manager: ProcessManager,
    ):
        shared.reset()
        global called
        called = 0

        class MySubjectMechanism(SubjectMechanism):
            def run(self):
                global called
                called += 1
                return {'foo': 42}

        class MySubjectBehaviour1(SubjectBehaviour):
            use = [MySubjectMechanism]

            def run(self, data):
                return {'bar': data[MySubjectMechanism]['foo'] + 100}

        class MySubjectBehaviour2(SubjectBehaviour):
            use = [MySubjectMechanism]

            def run(self, data):
                return {'bar': data[MySubjectMechanism]['foo'] + 100}

        class MySubject(Subject):
            behaviours_classes = [MySubjectBehaviour1, MySubjectBehaviour2]

        simulation = Simulation(config)
        my_subject = MySubject(config, simulation)
        subjects = Subjects(simulation=simulation)
        subjects.append(my_subject)
        simulation.subjects = subjects

        cycle_manager = CycleManager(
            config,
            logger,
            simulation=simulation,
            process_manager=do_nothing_process_manager,
        )
        cycle_manager._job_subjects(worker_id=0, process_count=1)
        assert called == 1

    def test_mechanism_called_once_for_multiple_simulation_behaviors(
        self,
        do_nothing_process_manager: ProcessManager,
    ):
        shared.reset()
        global called
        called = 0

        class MySimulationMechanism(SimulationMechanism):
            def run(self, process_number: int = None, process_count: int = None):
                global called
                called += 1
                return {'foo': 42}

        class MySimulationBehaviour1(SimulationBehaviour):
            use = [MySimulationMechanism]

            def run(self, data):
                return {'bar': data[MySimulationMechanism]['foo'] + 100}

        class MySimulationBehaviour2(SimulationBehaviour):
            use = [MySimulationMechanism]

            def run(self, data):
                return {'bar': data[MySimulationMechanism]['foo'] + 100}

        class MySimulation(Simulation):
            behaviours_classes = [MySimulationBehaviour1, MySimulationBehaviour2]

        simulation = MySimulation(config)
        subjects = Subjects(simulation=simulation)
        simulation.subjects = subjects

        cycle_manager = CycleManager(
            config,
            logger,
            simulation=simulation,
            process_manager=do_nothing_process_manager,
        )
        cycle_manager._job_simulation(worker_id=0, process_count=1)
        assert called == 1

    def test_mechanism_not_called_if_no_subject_behavior(
        self,
        do_nothing_process_manager: ProcessManager,
    ):
        shared.reset()
        global called
        called = 0

        class MySubjectMechanism(SubjectMechanism):
            def run(self):
                global called
                called += 1
                return {'foo': 42}

        class MySubject(Subject):
            behaviours_classes = []

        simulation = Simulation(config)
        my_subject = MySubject(config, simulation)
        subjects = Subjects(simulation=simulation)
        subjects.append(my_subject)
        simulation.subjects = subjects

        cycle_manager = CycleManager(
            config,
            logger,
            simulation=simulation,
            process_manager=do_nothing_process_manager,
        )
        cycle_manager._job_subjects(worker_id=0, process_count=1)
        assert called == 0

    def test_mechanism_not_called_if_no_simulation_behavior(
        self,
        do_nothing_process_manager: ProcessManager,
    ):
        shared.reset()
        global called
        called = 0

        class MySimulationMechanism(SimulationMechanism):
            def run(self, process_number: int = None, process_count: int = None):
                global called
                called += 1
                return {'foo': 42}

        class MySimulation(Simulation):
            pass

        simulation = MySimulation(config)
        subjects = Subjects(simulation=simulation)
        simulation.subjects = subjects

        cycle_manager = CycleManager(
            config,
            logger,
            simulation=simulation,
            process_manager=do_nothing_process_manager,
        )
        cycle_manager._job_simulation(worker_id=0, process_count=1)
        assert called == 0

    def test_mechanism_not_called_if_subject_behavior_cycled_not_active_yet(
        self,
        do_nothing_process_manager: ProcessManager,
    ):
        shared.reset()
        global called
        called = 0

        class MySubjectMechanism(SubjectMechanism):
            def run(self):
                global called
                called += 1
                return {'foo': 42}

        class MySubjectBehaviour1(SubjectBehaviour):
            use = [MySubjectMechanism]

            @property
            def cycle_frequency(self):
                return 2

            def run(self, data):
                return {'bar': data[MySubjectMechanism]['foo'] + 100}

        class MySubject(Subject):
            behaviours_classes = [MySubjectBehaviour1]

        simulation = Simulation(config)
        my_subject = MySubject(config, simulation)
        subjects = Subjects(simulation=simulation)
        subjects.append(my_subject)
        simulation.subjects = subjects

        cycle_manager = CycleManager(
            config,
            logger,
            simulation=simulation,
            process_manager=do_nothing_process_manager,
        )

        cycle_manager.current_cycle = 0
        cycle_manager._job_subjects(worker_id=0, process_count=1)
        assert called == 1

        cycle_manager.current_cycle = 1
        cycle_manager._job_subjects(worker_id=0, process_count=1)
        assert called == 1

        cycle_manager.current_cycle = 2
        cycle_manager._job_subjects(worker_id=0, process_count=1)
        assert called == 2

        cycle_manager.current_cycle = 3
        cycle_manager._job_subjects(worker_id=0, process_count=1)
        assert called == 2

    def test_mechanism_not_called_if_simulation_behavior_cycled_not_active_yet(
        self,
        do_nothing_process_manager: ProcessManager,
    ):
        shared.reset()

        pass

    def test_mechanism_not_called_if_subject_behavior_timebase_not_active_yet(
        self,
        do_nothing_process_manager: ProcessManager,
    ):
        shared.reset()

        pass

    def test_mechanism_not_called_if_simulation_behavior_timebase_not_active_yet(
        self,
        do_nothing_process_manager: ProcessManager,
    ):
        shared.reset()

        pass


# TODO: Test Simulation mechanism parralelisation
# TODO: Test behaviour actions generation
