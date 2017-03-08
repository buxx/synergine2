# coding: utf-8
from sandbox.engulf.behaviour import GrowUp, SearchGrass, EatGrass, Explore, CellBehaviourSelector, Hungry, Attack
from sandbox.engulf.const import COLLECTION_CELL, COLLECTION_ALIVE, COLLECTION_EATABLE, COLLECTION_GRASS, \
    COLLECTION_PREY, COLLECTION_PREDATOR
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
        Explore,
        Hungry,
    ]
    behaviour_selector_class = CellBehaviourSelector

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._appetite = self.config.simulation.start_appetite  # /100

    @property
    def appetite(self) -> float:
        return self._appetite

    @appetite.setter
    def appetite(self, value) -> None:
        if value > 100:
            self._appetite = 100
        elif value < 0:
            self._appetite = 0
        else:
            self._appetite = value


class PreyCell(Cell):
    collections = Cell.collections[:] + [COLLECTION_PREY]
    behaviours_classes = Cell.behaviours_classes[:] + [SearchGrass, EatGrass]


class PredatorCell(Cell):
    collections = Cell.collections[:] + [COLLECTION_PREDATOR]
    behaviours_classes = Cell.behaviours_classes[:] + [Attack]


class Grass(XYZSubjectMixin, Subject):
    collections = [
        COLLECTION_EATABLE,
        COLLECTION_GRASS,
    ]
    behaviours_classes = [
        GrowUp,
    ]

    def __init__(self, *args, **kwargs):
        self._density = kwargs.pop('density', 100.0)
        super().__init__(*args, **kwargs)

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
