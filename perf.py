

"""
Produce performance measurement
"""
import argparse
import multiprocessing
import os

import time

from sandbox.perf.simulation import ComputeSubject
from synergine2.config import Config
from synergine2.cycle import CycleManager
from synergine2.log import SynergineLogger
from synergine2.simulation import Simulation, Subjects


def simulate(complexity, subject_count, cycle_count, cores):
    config = Config(dict(complexity=complexity, use_x_cores=cores))
    simulation = Simulation(config)

    subjects = Subjects(simulation=simulation)
    for i in range(subject_count):
        subjects.append(ComputeSubject(
            config=config,
            simulation=simulation,
        ))

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
    # subject_counts = [10, 100, 1000, 2000, 5000]
    subject_counts = [1, 5]
    # complexities = [100, 20000]
    # complexities = [1, 100]
    complexities = [1]
    max_cores = args.max_cores or host_cores

    results = []
    datas = {}

    for core_i in range(max_cores):
        core_count = core_i + 1
        for subject_count in subject_counts:
            for complexity in complexities:
                print('CORES: {}, SUBJECTS: {}, COMPLEXITY: {}'.format(
                    core_count, subject_count, complexity,
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

    for d_complexity, c_values in datas.items():
        data_file_name = 'DATA_{}'.format(str(d_complexity))
        try:
            os.unlink(data_file_name)
        except FileNotFoundError:
            pass
        with open(data_file_name, 'w+') as file:
            file.writelines(['# (COMPLEXITY {}) SUBJECTS CORES_{}\n'.format(
                str(d_complexity),
                ' CORES_'.join(map(str, c_values.keys())),
            )])
            for d_subject_count, d_cores in c_values.items():
                line = '{} {}\n'.format(
                    str(d_subject_count),
                    ' '.join(map(str, d_cores.values())),
                )
                file.writelines([line])

    """
    gnuplot -p -e "set title \"COMPLEXITY_1\";
    plot 'DATA_1' using 1:2 title 'CORE_1' with lines,
    'DATA_1' using 1:3 title 'CORE_2' with lines"
    """

if __name__ == '__main__':
    main()
