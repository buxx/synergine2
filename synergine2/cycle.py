# coding: utf-8
import multiprocessing

from synergine2.config import Config
from synergine2.log import SynergineLogger
from synergine2.processing import ProcessManager
from synergine2.simulation import SimulationMechanism
from synergine2.simulation import SimulationBehaviour
from synergine2.simulation import Simulation
from synergine2.simulation import SubjectBehaviour
from synergine2.simulation import SubjectMechanism
from synergine2.simulation import Event
from synergine2.utils import ChunkManager


class CycleManager(object):
    def __init__(
            self,
            config: Config,
            logger: SynergineLogger,
            simulation: Simulation,
            process_manager: ProcessManager=None,
    ):
        if process_manager is None:
            process_manager = ProcessManager(
                process_count=multiprocessing.cpu_count(),
                chunk_manager=ChunkManager(multiprocessing.cpu_count()),
            )

        self.config = config
        self.logger = logger
        self.simulation = simulation
        self.process_manager = process_manager
        self.current_cycle = -1
        self.first_cycle = True

    def next(self) -> [Event]:
        if self.first_cycle:
            # To dispatch subjects add/removes, enable track on them
            self.simulation.subjects.track_changes = True
            self.first_cycle = False
        self.current_cycle += 1

        self.logger.info('Process cycle {}'.format(self.current_cycle))

        events = []
        # TODO: gestion des behaviours non parallelisables
        # TODO: Proposer des ordres d'execution
        events.extend(self._get_subjects_events())
        events.extend(self._get_simulation_events())

        self.logger.info('Cycle {} generate {} events'.format(
            str(self.current_cycle),
            str(len(events)),
        ))
        return events

    def _get_simulation_events(self) -> [Event]:
        events = []
        results = {}

        self.logger.info('Process simulation events')

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

        self.logger.info('Simulation generate {} behaviours'.format(len(results)))

        # Make events
        for behaviour_class, behaviour_data in results.items():
            behaviour_events = self.simulation.behaviours[behaviour_class].action(behaviour_data)
            self.logger.info('{} behaviour generate {} events'.format(
                str(behaviour_class),
                str(len(behaviour_events)),
            ))

            if self.logger.is_debug:
                self.logger.debug('{} behaviour generated events: {}'.format(
                    str(behaviour_class),
                    str([e.repr_debug() for e in behaviour_events]),
                ))

            events.extend(behaviour_events)

        self.logger.info('Simulation behaviours generate {} events'.format(len(events)))
        return events

    def _get_subjects_events(self) -> [Event]:
        events = []
        results = {}

        self.logger.info('Process subjects events')

        results_by_processes = self.process_manager.chunk_and_execute_jobs(
            data=self.simulation.subjects,
            job_maker=self.subjects_computing,
        )

        for process_results in results_by_processes:
            results.update(process_results)

        # Duplicate list to prevent conflicts with behaviours subjects manipulations
        for subject in self.simulation.subjects[:]:
            for behaviour_class, behaviour_data in results.get(subject.id, {}).items():
                # TODO: Ajouter une etape de selection des actions a faire (genre neuronnal)
                # (genre se cacher et fuir son pas compatibles)
                behaviour_events = subject.behaviours[behaviour_class].action(behaviour_data)

                self.logger.info('{} behaviour for subject {} generate {} events'.format(
                    str(behaviour_class),
                    str(subject.id),
                    str(len(behaviour_events)),
                ))

                if self.logger.is_debug:
                    self.logger.debug('{} behaviour for subject {} generated events: {}'.format(
                        str(behaviour_class),
                        str(subject.id),
                        str([e.repr_debug() for e in behaviour_events]),
                    ))

                events.extend(behaviour_events)

        self.logger.info('Subjects behaviours generate {} events'.format(len(events)))
        return events

    def simulation_computing(
            self,
            simulation,
            process_number,
            process_count,
    ):
        self.logger.info('Simulation computing')

        # TODO: necessaire de passer simulation ?
        mechanisms = self.get_mechanisms_to_compute(simulation)
        mechanisms_data = {}
        behaviours_data = {}

        self.logger.info('{} mechanisms to compute'.format(str(len(mechanisms))))
        if self.logger.is_debug:
            self.logger.debug('Mechanisms are: {}'.format(
                str([m.repr_debug() for m in mechanisms])
            ))

        for mechanism in mechanisms:
            mechanism_data = mechanism.run(
                process_number=process_number,
                process_count=process_count,
            )

            if self.logger.is_debug:
                self.logger.debug('{} mechanism product data: {}'.format(
                    type(mechanism).__name__,
                    str(mechanism_data),
                ))

            mechanisms_data[type(mechanism)] = mechanism_data

        behaviours = self.get_behaviours_to_compute(simulation)
        self.logger.info('{} behaviours to compute'.format(str(len(behaviours))))

        if self.logger.is_debug:
            self.logger.debug('Behaviours are: {}'.format(
                str([b.repr_debug() for b in behaviours])
            ))

        for behaviour in behaviours:
            behaviour_data = behaviour.run(mechanisms_data)  # TODO: Behaviours dependencies
            if self.logger.is_debug:
                self.logger.debug('{} behaviour produce data: {}'.format(
                    type(behaviour).__name__,
                    behaviour_data,
                ))

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
        self.logger.info('Subjects computing: {} subjects to compute'.format(str(len(subjects))))

        for subject in subjects:
            mechanisms = self.get_mechanisms_to_compute(subject)
            if not mechanisms:
                break

            self.logger.info('Subject {}: {} mechanisms'.format(
                str(subject.id),
                str(len(mechanisms)),
            ))

            if self.logger.is_debug:
                self.logger.info('Subject {}: mechanisms are: {}'.format(
                    str(subject.id),
                    str([m.repr_debug for m in mechanisms])
                ))

            mechanisms_data = {}
            behaviours_data = {}

            for mechanism in mechanisms:
                mechanism_data = mechanism.run()
                if self.logger.is_debug:
                    self.logger.info('Subject {}: {} mechanisms produce data: {}'.format(
                        str(subject.id),
                        type(mechanism).__name__,
                        str(mechanism_data),
                    ))

                mechanisms_data[type(mechanism)] = mechanism_data

            if self.logger.is_debug:
                self.logger.info('Subject {}: mechanisms data are: {}'.format(
                    str(subject.id),
                    str(mechanisms_data),
                ))

            subject_behaviours = self.get_behaviours_to_compute(subject)

            self.logger.info('Subject {}: have {} behaviours'.format(
                str(subject.id),
                str(len(subject_behaviours)),
            ))

            for behaviour in subject_behaviours:
                self.logger.info('Subject {}: run {} behaviour'.format(
                    str(subject.id),
                    str(type(behaviour)),
                ))

                # We identify behaviour data with it's class to be able to intersect it after subprocess data collect
                behaviour_data = behaviour.run(mechanisms_data)  # TODO: Behaviours dependencies

                if self.logger.is_debug:
                    self.logger.debug('Subject {}: behaviour {} produce data: {}'.format(
                        str(type(behaviour)),
                        str(subject.id),
                        str(behaviour_data),
                    ))

                if behaviour_data:
                    behaviours_data[type(behaviour)] = behaviour_data

            results[subject.id] = behaviours_data
        return results

    def get_mechanisms_to_compute(self, mechanisable) -> [SubjectMechanism, SimulationMechanism]:
        # TODO: Implementer un systeme qui inhibe des mechanisme (ex. someil inhibe l'ouie)
        return mechanisable.mechanisms.values()

    def get_behaviours_to_compute(self, mechanisable) -> [SubjectBehaviour, SimulationBehaviour]:
        # TODO: Implementer un systeme qui inhibe des behaviours (ex. someil inhibe avoir faim)
        behaviours = list(mechanisable.behaviours.values())

        for behaviour in behaviours[:]:
            if behaviour.frequency != 1:
                if self.current_cycle % behaviour.frequency:
                    behaviours.remove(behaviour)

        return behaviours

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
        self.logger.info('Apply {} simulation_actions and {} subject_actions'.format(
            len(simulation_actions),
            len(subject_actions),
        ))

        for subject_id, behaviours_and_data in subject_actions:
            subject = self.simulation.subjects.index.get(subject_id)
            for behaviour_class, behaviour_data in behaviours_and_data:
                behaviour = behaviour_class(
                    simulation=self.simulation,
                    subject=subject,
                )
                self.logger.info('Apply {} behaviour on subject {}'.format(
                    str(behaviour_class),
                    str(subject_id),
                ))
                if self.logger.is_debug:
                    self.logger.debug('{} behaviour data is {}'.format(
                        str(behaviour_class),
                        str(behaviour_data),
                    ))
                behaviour_events = behaviour.action(behaviour_data)
                self.logger.info('{} events from behaviour {} from subject {}'.format(
                    len(behaviour_events),
                    str(behaviour_class),
                    str(subject_id),
                ))
                if self.logger.is_debug:
                    self.logger.debug('Events from behaviour {} from subject {} are: {}'.format(
                        str(behaviour_class),
                        str(subject_id),
                        str([e.repr_debug() for e in behaviour_events])
                    ))
                events.extend(behaviour_events)

        for behaviour_class, behaviour_data in simulation_actions:
            behaviour = behaviour_class(
                simulation=self.simulation,
            )

            self.logger.info('Apply {} simulation behaviour'.format(
                str(behaviour_class),
            ))

            behaviour_events = behaviour.action(behaviour_data)
            if self.logger.is_debug:
                self.logger.debug('Events from behaviour {} are: {}'.format(
                    str(behaviour_class),
                    str([e.repr_debug() for e in behaviour_events])
                ))

            events.extend(behaviour_events)

        self.logger.info('{} events generated'.format(len(events)))
        return events
