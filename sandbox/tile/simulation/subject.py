# coding: utf-8
from sandbox.tile.const import COLLECTION_ALIVE
from sandbox.tile.simulation.base import BaseSubject
from sandbox.tile.simulation.behaviour import MoveToBehaviour
from sandbox.tile.simulation.behaviour import LookAroundBehaviour
from synergine2.share import shared


class TileSubject(BaseSubject):
    start_collections = [
        COLLECTION_ALIVE,
    ]
    behaviours_classes = [
        MoveToBehaviour,
        LookAroundBehaviour,
    ]
    visible_opponent_ids = shared.create_self('visible_opponent_ids', lambda: [])
    # TODO: implement (copied from engulf)
    # behaviour_selector_class = CellBehaviourSelector
