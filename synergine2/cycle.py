import multiprocessing

from synergine2.processing import ProcessManager
from synergine2.simulation import Subject, Behaviour, Mechanism
from synergine2.utils import ChunkManager


class CycleManager(object):
    def __init__(
            self,
            subjects: list,
            process_manager: ProcessManager=None,
    ):
        if process_manager is None:
            process_manager = ProcessManager(
                process_count=multiprocessing.cpu_count(),
                chunk_manager=ChunkManager(multiprocessing.cpu_count()),
                job_maker=self.computing,
            )

        self.subjects = subjects
        self._process_manager = process_manager
        self._current_cycle = 0

    def next(self):
        results = {}
        results_by_processes = self._process_manager.execute_jobs(self.subjects)
        for process_results in results_by_processes:
            results.update(process_results)
        for subject in self.subjects[:]:  # Duplicate list to prevent conflicts with behaviours subjects manipulations
            for behaviour_class in results[subject.id]:
                # TODO: Ajouter une etape de selection des actions a faire (genre neuronnal)
                # TODO: les behaviour_class ont le même uniqueid apres le process ?
                subject.behaviours[behaviour_class].action(results[subject.id][behaviour_class])

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
