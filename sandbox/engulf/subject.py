from synergine2.simulation import Subject
from synergine2.xyz import XYZSubjectMixin

COLLECTION_CELL = 'CELL'
COLLECTION_ALIVE = 'ALIVE'


class Cell(XYZSubjectMixin, Subject):
    collections = [
        COLLECTION_CELL,
        COLLECTION_ALIVE,
    ]
