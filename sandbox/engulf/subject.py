from synergine2.simulation import Subject
from synergine2.xyz import XYZSubjectMixin

COLLECTION_CELL = 'CELL'
COLLECTION_ALIVE = 'ALIVE'
COLLECTION_EATABLE = 'EATABLE'


class Cell(XYZSubjectMixin, Subject):
    collections = [
        COLLECTION_CELL,
        COLLECTION_ALIVE,
        COLLECTION_EATABLE,
    ]


class Grass(XYZSubjectMixin, Subject):
    collections = [
        COLLECTION_EATABLE,
    ]
