import random

from synergine2.config import Config
from synergine2.share import shared
from synergine2.simulation import SubjectMechanism, SubjectBehaviour, Event, Subject


def compute(complexity: int):
    random_floats = []
    result = 0.0

    for i in range(complexity):
        random_floats.append(random.uniform(0, 100))

    for j, random_float in enumerate(random_floats):
        if not j % 2:
            result += random_float
        else:
            result -= random_float

    return result


class ComputeMechanism(SubjectMechanism):
    def run(self):
        complexity = self.config.get('complexity')
        value = compute(complexity)

        return {
            'mechanism_value': value,
            'complexity': complexity,
        }


class ComplexityEvent(Event):
    def __init__(self, complexity, *args, **kwargs):
        self.complexity = complexity


class ComputeBehaviour(SubjectBehaviour):
    use = [ComputeMechanism]

    def run(self, data):
        return not data.get('ComputeMechanism').get('mechanism_value') % 2

    def action(self, data):
        mechanism_value = data.get('ComputeMechanism').get('mechanism_value')
        complexity = data.get('ComputeMechanism').get('complexity')

        if not int(str(mechanism_value)[-1]) % 2:
            compute(complexity)

        return [Event(complexity)]


class ComputeSubject(Subject):
    behaviours_classes = [ComputeBehaviour]
    data = shared.create(['{id}', 'data'], [])

    def __init__(
        self,
        config: Config,
        simulation: 'Simulation',
    ):
        super().__init__(config, simulation)
