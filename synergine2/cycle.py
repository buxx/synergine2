import multiprocessing

from synergine2.processing import ProcessManager
from synergine2.simulation import Subject, SimulationMechanism, SimulationBehaviour
from synergine2.simulation import Simulation
from synergine2.simulation import SubjectBehaviour
from synergine2.simulation import SubjectMechanism
from synergine2.simulation import Event
from synergine2.utils import ChunkManager


class CycleManager(object):
    def __init__(
            self,
            simulation: Simulation,
            process_manager: ProcessManager=None,
    ):
        if process_manager is None:
            process_manager = ProcessManager(
                process_count=multiprocessing.cpu_count(),
                chunk_manager=ChunkManager(multiprocessing.cpu_count()),
            )

        self.simulation = simulation
        self.process_manager = process_manager
        self.current_cycle = 0
        self.first_cycle = True

    def next(self) -> [Event]:
        if self.first_cycle:
            # To dispatch subjects add/removes, enable track on them
            self.simulation.subjects.track_changes = True
            self.first_cycle = False

        events = []
        # TODO: gestion des behaviours non parallelisables
        # TODO: Proposer des ordres d'execution
        events.extend(self._get_subjects_events())
        events.extend(self._get_simulation_events())

        return events

    def _get_simulation_events(self) -> [Event]:
        events = []
        results = {}
        results_by_processes = self.process_manager.execute_jobs(
            data=self.simulation,
            job_maker=self.simulation_computing,
        )

        for process_result in results_by_processes:
            for behaviour_class, behaviour_result in process_result.items():
                results[behaviour_class] = behaviour_class.merge_data(
                    behaviour_result,
                    results.get(behaviour_class),
                )

        # Make events
        for behaviour_class, behaviour_data in results.items():
            events.extend(self.simulation.behaviours[behaviour_class].action(behaviour_data))

        return events

    def _get_subjects_events(self) -> [Event]:
        events = []
        results_by_processes = self.process_manager.chunk_and_execute_jobs(
            data=self.simulation.subjects,
            job_maker=self.subjects_computing,
        )
        results = {}
        for process_results in results_by_processes:
            results.update(process_results)
        for subject in self.simulation.subjects[:]:  # Duplicate list to prevent conflicts with behaviours subjects manipulations
            for behaviour_class, behaviour_data in results[subject.id].items():
                # TODO: Ajouter une etape de selection des actions a faire (genre neuronnal)
                # (genre se cacher et fuir son pas compatibles)
                actions_events = subject.behaviours[behaviour_class].action(behaviour_data)
                events.extend(actions_events)

        return events

    def simulation_computing(
            self,
            simulation,
            process_number,
            process_count,
    ):
        # TODO: necessaire de passer simulation ?
        mechanisms = self.get_mechanisms_to_compute(simulation)
        mechanisms_data = {}
        behaviours_data = {}

        for mechanism in mechanisms:
            mechanisms_data[type(mechanism)] = mechanism.run(
                process_number=process_number,
                process_count=process_count,
            )

        for behaviour in self.get_behaviours_to_compute(simulation):
            behaviour_data = behaviour.run(mechanisms_data)  # TODO: Behaviours dependencies
            if behaviour_data:
                behaviours_data[type(behaviour)] = behaviour_data

        return behaviours_data

    def subjects_computing(
            self,
            subjects,
            process_number=None,
            process_count=None,
    ):
        results = {}
        for subject in subjects:
            mechanisms = self.get_mechanisms_to_compute(subject)
            mechanisms_data = {}
            behaviours_data = {}

            for mechanism in mechanisms:
                mechanisms_data[type(mechanism)] = mechanism.run()

            for behaviour in self.get_behaviours_to_compute(subject):
                # We identify behaviour data with it's class to be able to intersect it after subprocess data collect
                behaviour_data = behaviour.run(mechanisms_data)  # TODO: Behaviours dependencies
                if behaviour_data:
                    behaviours_data[type(behaviour)] = behaviour_data

            results[subject.id] = behaviours_data
        return results

    def get_mechanisms_to_compute(self, mechanisable) -> [SubjectMechanism, SimulationMechanism]:
        # TODO: Implementer un systeme qui inhibe des mechanisme (ex. someil inhibe l'ouie)
        return mechanisable.mechanisms.values()

    def get_behaviours_to_compute(self, mechanisable) -> [SubjectBehaviour, SimulationBehaviour]:
        # TODO: Implementer un systeme qui inhibe des behaviours (ex. someil inhibe avoir faim)
        return mechanisable.behaviours.values()

    def apply_actions(
            self,
            simulation_actions: [tuple]=None,
            subject_actions: [tuple]=None,
    ) -> [Event]:
        """
        TODO: bien specifier la forme des parametres
        simulation_actions = [(class, {'data': 'foo'})]
        subject_actions = [(subject_id, [(class, {'data': 'foo'}])]
        """
        simulation_actions = simulation_actions or []
        subject_actions = subject_actions or []
        events = []

        for subject_id, behaviours_and_data in subject_actions:
            subject = self.simulation.subjects.index.get(subject_id)
            for behaviour_class, behaviour_data in behaviours_and_data:
                behaviour = behaviour_class(
                    simulation=self.simulation,
                    subject=subject,
                )
                events.extend(behaviour.action(behaviour_data))

        for behaviour_class, behaviour_data in simulation_actions:
            behaviour = behaviour_class(
                simulation=self.simulation,
            )
            events.extend(behaviour.action(behaviour_data))

        return events
