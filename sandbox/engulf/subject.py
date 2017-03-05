# coding: utf-8
from sandbox.engulf.behaviour import GrowUp, SearchFood, Eat, Explore, CellBehaviourSelector
from sandbox.engulf.const import COLLECTION_CELL, COLLECTION_ALIVE, COLLECTION_EATABLE, COLLECTION_GRASS
from synergine2.simulation import Subject
from synergine2.xyz import XYZSubjectMixin


class Cell(XYZSubjectMixin, Subject):
    collections = [
        COLLECTION_CELL,
        COLLECTION_ALIVE,
        COLLECTION_EATABLE,
    ]
    # TODO: Mettre en place la "selection/choix": car il y a deux move possible chaque cycle ci-dessous.
    behaviours_classes = [
        SearchFood,
        Eat,
        Explore,
    ]
    behaviour_selector_class = CellBehaviourSelector


class Grass(XYZSubjectMixin, Subject):
    collections = [
        COLLECTION_EATABLE,
        COLLECTION_GRASS,
    ]
    behaviours_classes = [
        GrowUp,
    ]

    def __init__(self, *args, density=100.0, **kwargs):
        super().__init__(*args, **kwargs)
        self._density = density

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
