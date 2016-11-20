import multiprocessing

from synergine2.processing import ProcessManager
from synergine2.simulation import Subject
from synergine2.simulation import Behaviour
from synergine2.simulation import Mechanism
from synergine2.simulation import Event
from synergine2.simulation import Subjects
from synergine2.utils import ChunkManager


class CycleManager(object):
    def __init__(
            self,
            subjects: Subjects,
            process_manager: ProcessManager=None,
    ):
        if process_manager is None:
            process_manager = ProcessManager(
                process_count=multiprocessing.cpu_count(),
                chunk_manager=ChunkManager(multiprocessing.cpu_count()),
                job_maker=self.computing,
            )

        self.subjects = subjects
        self.process_manager = process_manager
        self.current_cycle = 0
        self.first_cycle = True

    def next(self) -> [Event]:
        if self.first_cycle:
            # To dispatch subjects add/removes, enable track on them
            self.subjects.track_changes = True
            self.first_cycle = False

        results = {}
        results_by_processes = self.process_manager.execute_jobs(self.subjects)
        events = []
        for process_results in results_by_processes:
            results.update(process_results)
        for subject in self.subjects[:]:  # Duplicate list to prevent conflicts with behaviours subjects manipulations
            for behaviour_class in results[subject.id]:
                # TODO: Ajouter une etape de selection des actions a faire (genre neuronnal)
                # (genre se cacher et fuir son pas compatibles)
                actions_events = subject.behaviours[behaviour_class].action(results[subject.id][behaviour_class])
                events.extend(actions_events)

        return events

    def computing(self, subjects):
        # compute mechanisms (prepare check to not compute slienced or not used mechanisms)
        # compute behaviours with mechanisms data
        # return list with per subject: [behaviour: return, behaviour: return] if behaviour return True something
        results = {}
        for subject in subjects:
            mechanisms = self.get_mechanisms_to_compute(subject)
            mechanisms_data = {}
            behaviours_data = {}

            for mechanism in mechanisms:
                mechanisms_data[type(mechanism)] = mechanism.run()

            for behaviour in self.get_behaviours_to_compute(subject):
                # We identify behaviour data with it's class to be able to intersect it after subprocess data collect
                behaviour_data = behaviour.run(mechanisms_data)
                if behaviour_data:
                    behaviours_data[type(behaviour)] = behaviour_data

            results[subject.id] = behaviours_data
            # TODO: Tester les performances si on utilise un index numerique pour les results[subject]
            # et behaviours_data[type(behaviours_data)]
        return results

    def get_mechanisms_to_compute(self, subject: Subject) -> [Mechanism]:
        # TODO: Implementer un systeme qui inhibe des mechanisme (ex. someil inhibe l'ouie)
        return subject.mechanisms.values()

    def get_behaviours_to_compute(self, subject: Subject) -> [Behaviour]:
        # TODO: Implementer un systeme qui inhibe des behaviours (ex. someil inhibe avoir faim)
        return subject.behaviours.values()
