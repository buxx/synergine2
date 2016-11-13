

class ChunkManager(object):
    def __init__(self, chunks_numbers: int):
        self._chunks_numbers = chunks_numbers

    def make_chunks(self, data: list) -> list:
        i, j, x = len(data), 0, []
        for k in range(self._chunks_numbers):
            a, j = j, j + (i + k) // self._chunks_numbers
            x.append(data[a:j])
        return x


def get_mechanisms_classes(subject: 'Subject') -> ['Mechanisms']:
    mechanisms_classes = []
    for behaviour_class in subject.behaviours_classes:
        mechanisms_classes.extend(behaviour_class.use)
    return list(set(mechanisms_classes))  # Remove duplicates


def initialize_subject(
        simulation: 'Simulation',
        subject: 'Subject',
) -> None:
    for mechanism_class in get_mechanisms_classes(subject):
        subject.mechanisms[mechanism_class] = mechanism_class(
            simulation=simulation,
            subject=subject,
        )

    for behaviour_class in subject.behaviours_classes:
        subject.behaviours[behaviour_class] = behaviour_class(
            simulation=simulation,
            subject=subject,
        )
