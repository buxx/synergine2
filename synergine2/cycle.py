# coding: utf-8
import multiprocessing
import typing

from synergine2.base import BaseObject
from synergine2.config import Config
from synergine2.exceptions import SynergineException
from synergine2.log import SynergineLogger
from synergine2.processing import ProcessManager
from synergine2.share import shared
from synergine2.simulation import Subject
from synergine2.simulation import Simulation
from synergine2.simulation import SubjectBehaviour
from synergine2.simulation import SubjectMechanism
from synergine2.simulation import Event
from synergine2.utils import time_it


JOB_TYPE_SUBJECTS = 0
JOB_TYPE_SIMULATION = 1


class CycleManager(BaseObject):
    def __init__(
            self,
            config: Config,
            logger: SynergineLogger,
            simulation: Simulation,
            process_manager: ProcessManager=None,
    ):
        # TODO: reproduire le mechanisme d'index de behaviour/etc pour simulation
        self.config = config
        self.logger = logger
        self.simulation = simulation
        self.current_cycle = -1
        self.first_cycle = True

        # TODO NOW: Les processes devront maintenir une liste des subjects qui sont nouveaux.ne connaissent pas
        # Attention a ce qu'in ne soient pas "expose" quand on créer ces subjects au sein du process.
        # Ces subjects ont vocation à adopter l'id du vrau subject tout de suite après leur instanciation
        if process_manager is None:
            process_manager = ProcessManager(
                config=config,
                # TODO: Changer de config de merde (core.use_x_cores)
                process_count=config.get('core', {}).get('use_x_cores', multiprocessing.cpu_count()),
                job=self.job,
            )
        self.process_manager = process_manager

    def job(self, worker_id: int, process_count: int, job_type: str) -> 'TODO':
        # ICI: (in process) on doit avoir:
        # La tranche x:y de sujets à traiter
        shared.refresh()
        if job_type == JOB_TYPE_SUBJECTS:
            return self._job_subjects(worker_id, process_count)
        if job_type == JOB_TYPE_SIMULATION:
            return self._job_simulation(worker_id, process_count)
        raise SynergineException('Unknown job type "{}"'.format(job_type))

    def _job_subjects(self, worker_id: int, process_count: int) -> typing.Dict[int, typing.Dict[str, typing.Any]]:
        # Determine list of process subject to work with
        subject_ids = shared.get('subject_ids')
        chunk_length, rest = divmod(len(subject_ids), process_count)

        from_ = chunk_length * worker_id
        to_ = from_ + chunk_length

        if worker_id + 1 == process_count:
            to_ += rest

        subject_ids_to_parse = subject_ids[from_:to_]

        # Build list of subjects for compute them
        subjects = []
        for subject_id in subject_ids_to_parse:
            subject = self.simulation.get_or_create_subject(subject_id)
            subjects.append(subject)

        results_by_subjects = self._subjects_computing(subjects)
        return results_by_subjects

    def _job_simulation(self, worker_id: int, process_count: int) -> typing.Dict[int, typing.Dict[str, typing.Any]]:
        self.logger.info('Simulation computing (worker {})'.format(worker_id))

        mechanisms = self.simulation.mechanisms.values()
        mechanisms_data = {}
        behaviours_data = {}

        self.logger.info('{} mechanisms to compute'.format(str(len(mechanisms))))
        if self.logger.is_debug:
            self.logger.debug('Mechanisms are: {}'.format(
                str([m.repr_debug() for m in mechanisms])
            ))

        for mechanism in mechanisms:
            mechanism_data = mechanism.run(
                process_number=worker_id,
                process_count=process_count,
            )

            if self.logger.is_debug:
                self.logger.debug('{} mechanism product data: {}'.format(
                    type(mechanism).__name__,
                    str(mechanism_data),
                ))

            mechanisms_data[mechanism.__class__] = mechanism_data

        behaviours = self.simulation.behaviours.values()
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
                behaviours_data[behaviour.__class__] = behaviour_data

        return behaviours_data

    def next(self) -> [Event]:
        if self.first_cycle:
            # To dispatch subjects add/removes, enable track on them
            self.simulation.subjects.track_changes = True
            self.first_cycle = False
        self.current_cycle += 1

        self.logger.info('Process cycle {}'.format(self.current_cycle))

        events = []
        shared.commit()

        # TODO: gestion des behaviours non parallelisables
        # TODO: Proposer des ordres d'execution
        with time_it() as elapsed_time:
            events.extend(self._get_subjects_events())
        print('Cycle subjects events duration: {}s'.format(elapsed_time.get_final_time()))

        with time_it() as elapsed_time:
            events.extend(self._get_simulation_events())
        print('Cycle simulation events duration: {}s'.format(elapsed_time.get_final_time()))

        self.logger.info('Cycle {} generate {} events'.format(
            str(self.current_cycle),
            str(len(events)),
        ))
        return events

    def _get_simulation_events(self) -> [Event]:
        events = []
        results = {}

        self.logger.info('Process simulation events')

        # TODO: Think about compute simulation cycle in workers
        results_by_processes = self.process_manager.make_them_work(JOB_TYPE_SIMULATION)

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
        results_by_processes = self.process_manager.make_them_work(JOB_TYPE_SUBJECTS)

        for process_results in results_by_processes:
            results.update(process_results)

        # Duplicate list to prevent conflicts with behaviours subjects manipulations
        for subject in self.simulation.subjects[:]:
            subject_behaviours_results = results.get(subject.id, {})
            if subject.behaviour_selector:
                # TODO: Looging
                subject_behaviours_results = subject.behaviour_selector.reduce_behaviours(dict(
                    subject_behaviours_results,
                ))

            subject_behaviours = subject.behaviours
            for behaviour_class, behaviour_data in subject_behaviours_results.items():
                # TODO: Ajouter une etape de selection des actions a faire (genre neuronnal)
                # (genre se cacher et fuir son pas compatibles)
                behaviour_events = subject_behaviours[behaviour_class].action(behaviour_data)

                self.logger.info('{} behaviour for subject {} generate {} events'.format(
                    str(behaviour_class.__name__),
                    str(subject.id),
                    str(len(behaviour_events)),
                ))

                if self.logger.is_debug:
                    self.logger.debug('{} behaviour for subject {} generated events: {}'.format(
                        str(behaviour_class.__name__),
                        str(subject.id),
                        str([e.repr_debug() for e in behaviour_events]),
                    ))

                events.extend(behaviour_events)

        self.logger.info('Subjects behaviours generate {} events'.format(len(events)))
        return events

    def _subjects_computing(
            self,
            subjects,
            process_number=None,
            process_count=None,
    ) -> typing.Dict[int, typing.Dict[str, typing.Any]]:
        results = {}
        self.logger.info('Subjects computing: {} subjects to compute'.format(str(len(subjects))))

        for subject in subjects:
            mechanisms = subject.mechanisms.values()

            if mechanisms:
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
                with time_it() as elapsed_time:
                    mechanism_data = mechanism.run()
                if self.logger.is_debug:
                    self.logger.debug('Subject {}: {} mechanisms produce data: {} in {}s'.format(
                        str(subject.id),
                        type(mechanism).__name__,
                        str(mechanism_data),
                        elapsed_time.get_final_time(),
                    ))

                mechanisms_data[mechanism.__class__] = mechanism_data

            if mechanisms:
                if self.logger.is_debug:
                    self.logger.info('Subject {}: mechanisms data are: {}'.format(
                        str(subject.id),
                        str(mechanisms_data),
                    ))

            subject_behaviours = subject.behaviours
            if not subject_behaviours:
                break

            self.logger.info('Subject {}: have {} behaviours'.format(
                str(subject.id),
                str(len(subject_behaviours)),
            ))

            for behaviour in subject_behaviours.values():
                self.logger.info('Subject {}: run {} behaviour'.format(
                    str(subject.id),
                    str(type(behaviour)),
                ))

                # We identify behaviour data with it's class to be able to intersect it after subprocess data collect
                with time_it() as elapsed_time:
                    behaviour_data = behaviour.run(mechanisms_data)  # TODO: Behaviours dependencies

                if self.logger.is_debug:
                    self.logger.debug('Subject {}: behaviour {} produce data: {} in {}s'.format(
                        str(type(behaviour)),
                        str(subject.id),
                        str(behaviour_data),
                        elapsed_time.get_final_time(),
                    ))

                if behaviour_data:
                    behaviours_data[behaviour.__class__] = behaviour_data

            results[subject.id] = behaviours_data
        return results

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
                config=self.config,
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

    def stop(self) -> None:
        self.process_manager.terminate()
