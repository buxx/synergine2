from sandbox.engulf.behaviour import GrowUp
from synergine2.simulation import Subject
from synergine2.xyz import XYZSubjectMixin

COLLECTION_CELL = 'CELL'
COLLECTION_ALIVE = 'ALIVE'
COLLECTION_EATABLE = 'EATABLE'
COLLECTION_GRASS = 'GRASS'


class Cell(XYZSubjectMixin, Subject):
    collections = [
        COLLECTION_CELL,
        COLLECTION_ALIVE,
        COLLECTION_EATABLE,
    ]


class Grass(XYZSubjectMixin, Subject):
    collections = [
        COLLECTION_EATABLE,
        COLLECTION_GRASS,
    ]
    behaviours_classes = [
        GrowUp,
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._density = 100.0

    @property
    def density(self) -> float:
        return self._density

    @density.setter
    def density(self, value: float) -> None:
        if value > 100:
            self._density = 100
        elif value < 0:
            self._density = 0
        else:
            self._density = value
