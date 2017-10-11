

"""
Produce performance measurement
"""
import argparse
import multiprocessing
import os

import time
from collections import OrderedDict
from random import randint

from sandbox.perf.simulation import ComputeSubject, ComputeBehaviour, ComputeMechanism
from synergine2.config import Config
from synergine2.cycle import CycleManager
from synergine2.log import SynergineLogger
from synergine2.simulation import Simulation, Subjects


def simulate(complexity, subject_count, cycle_count, cores):
    config = Config(dict(complexity=complexity, core=dict(use_x_cores=cores)))
    simulation = Simulation(config)
    subjects = Subjects(simulation=simulation)

    for i in range(subject_count):
        subject = ComputeSubject(
            config=config,
            simulation=simulation,
        )
        subject.data = [randint(0, 1000) for i in range(1000)]
        subjects.append(subject)

    simulation.subjects = subjects

    cycle_manager = CycleManager(
        config,
        SynergineLogger('perf'),
        simulation=simulation,
    )

    for j in range(cycle_count):
        cycle_manager.next()


def main():
    parser = argparse.ArgumentParser(description='Perf measures')
    parser.add_argument(
        '--max_cores',
        type=int,
        default=0,
        help='number of used cores',
    )

    args = parser.parse_args()

    host_cores = multiprocessing.cpu_count()
    retry = 1
    cycles = 10
    subject_counts = [500]
    complexities = [200]
    max_cores = args.max_cores or host_cores

    results = []
    datas = OrderedDict()

    for core_i in range(max_cores):
        # if core_i == 0:
        #     continue
        core_count = core_i + 1
        for subject_count in subject_counts:
            for complexity in complexities:
                print('COMPLEXITY: {}, SUBJECTS: {}, CORES: {}'.format(
                    complexity,
                    subject_count,
                    core_count,
                ), end='')

                durations = []
                for try_i in range(retry):
                    start_time = time.time()
                    simulate(complexity, subject_count, cycles, core_count)
                    durations.append(time.time() - start_time)
                duration = min(durations)

                result = {
                    'cores': core_count,
                    'complexity': complexity,
                    'subject_count': subject_count,
                    'cycles': cycles,
                    'duration': duration,
                    'duration_cycle': duration / cycles,
                    'duration_subj_complex': (duration / cycles) / (subject_count * complexity),
                }
                results.append(result)

                print(': {}s, {}s/c, {}s/C'.format(
                    result['duration'],
                    result['duration_cycle'],
                    result['duration_subj_complex'],
                ))
                datas.setdefault(complexity, {}).setdefault(subject_count, {})[core_count] = result['duration_cycle']

    for d_complexity, c_values in sorted(datas.items(), key=lambda e: int(e[0])):
        data_file_name = 'DATA_{}'.format(str(d_complexity))
        try:
            os.unlink(data_file_name)
        except FileNotFoundError:
            pass
        with open(data_file_name, 'w+') as file:
            file.writelines(['# (COMPLEXITY {}) SUBJECTS CORES_{}\n'.format(
                str(d_complexity),
                ' CORES_'.join(map(str, range(1, max_cores+1))),
            )])
            for d_subject_count, d_cores in c_values.items():
                line = '{} {}\n'.format(
                    str(d_subject_count),
                    ' '.join(map(str, d_cores.values())),
                )
                file.writelines([line])

        """
        subj_core = []
            for subj, core_v in c_values.items():
                for core_nb in core_v.keys():
                    subj_core.append((subj, core_nb))
            file.writelines(['# (COMPLEXITY {}) SUBJECTS CORES_{}\n'.format(
                str(d_complexity),
                ' '.join([
                    'SUBJ_{}_COR_{}'.format(
                        subj, core_nb,
                    ) for subj, core_nb in subj_core
                ])
            )])
        """

    for d_complexity, c_values in datas.items():
        print('')
        print('gnuplot -p -e "set title \\"COMPLEXITY_{}\\"; plot {}"'.format(
            str(d_complexity),
            ','.join([
                ' \'DATA_{}\' using 1:{} title \'CORE_{}\' with lines'.format(
                    d_complexity,
                    d_core+1,
                    d_core,
                ) for d_core in range(1, max_cores+1)
            ])
        ))


if __name__ == '__main__':
    main()
