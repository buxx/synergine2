# coding: utf-8
from sandbox.tile.const import COLLECTION_ALIVE
from sandbox.tile.simulation.base import BaseSubject
from synergine2_xyz.move import MoveToBehaviour


class Man(BaseSubject):
    collections = [
        COLLECTION_ALIVE,
    ]
    behaviours_classes = [
        MoveToBehaviour,
    ]
    # TODO: implement (copied from engulf)
    # behaviour_selector_class = CellBehaviourSelector
