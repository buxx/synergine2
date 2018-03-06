# coding: utf-8
from synergine2.config import Config
from synergine2.simulation import SubjectComposedBehaviour
from synergine2_xyz.simulation import XYZSimulation
from synergine2_xyz.subjects import XYZSubject
from tests import BaseTest


class MyComposedBehaviour(SubjectComposedBehaviour):
    pass


class TestComposedBehaviour(BaseTest):
    def test_subject_composed_behaviour(self):
        config = Config({})
        simulation = XYZSimulation(config)
        subject = XYZSubject()

        # TODO: !: Les donneés venant d el'intention doivent tjrs etre partagé (pls
        # process par exemple)
        my_composed_behaviour = MyComposedBehaviour(
            config=config,
            simulation=simulation,
            subject=subject,
        )
        my_composed_behaviour.run({
            'start': 0,
        })


