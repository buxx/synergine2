# coding: utf-8
# -*- coding: utf-8 -*-
from synergine2.config import Config
from synergine2.simulation import Subject
from synergine2.xyz import ProximitySubjectMechanism
from synergine2.xyz import XYZSubjects
from synergine2.xyz import XYZSimulation
from synergine2.xyz import XYZSubjectMixin
from synergine2.xyz_utils import get_positions_from_str_representation
from synergine2.xyz_utils import get_str_representation_from_positions
from tests import BaseTest
from tests import str_kwargs


class MySubject(XYZSubjectMixin, Subject):
    pass


class MyProximityMechanism(ProximitySubjectMechanism):
    distance = 10


class TestXYZ(BaseTest):
    def test_proximity_mechanism_with_one(self):
        simulation = XYZSimulation(Config())
        subject = MySubject(Config(), simulation, position=(0, 0, 0))
        other_subject = MySubject(Config(), simulation, position=(5, 0, 0))

        simulation.subjects = XYZSubjects(
            [subject, other_subject],
            simulation=simulation,
        )

        proximity_mechanism = MyProximityMechanism(
            config=Config(),
            simulation=simulation,
            subject=subject,
        )

        assert 5 == proximity_mechanism.get_distance_of(
            position=subject.position,
            subject=other_subject,
        )
        assert [{
            'subject': other_subject,
            'direction': 90.0,
            'distance': 5.0,
        }] == proximity_mechanism.run()

    def test_proximity_mechanism_excluding(self):
        simulation = XYZSimulation(Config())
        subject = MySubject(Config(), simulation, position=(0, 0, 0))
        other_subject = MySubject(Config(), simulation, position=(11, 0, 0))

        simulation.subjects = XYZSubjects(
            [subject, other_subject],
            simulation=simulation,
        )

        proximity_mechanism = MyProximityMechanism(
            config=Config(),
            simulation=simulation,
            subject=subject,
        )

        assert 11 == proximity_mechanism.get_distance_of(
            position=subject.position,
            subject=other_subject,
        )
        # other_subject is to far away
        assert [] == proximity_mechanism.run()

    def test_proximity_mechanism_with_multiple(self):
        simulation = XYZSimulation(Config())
        subject = MySubject(Config(), simulation, position=(0, 0, 0))
        other_subjects = []

        for i in range(3):
            other_subjects.append(MySubject(Config(), simulation, position=(i, i, 0)))

        simulation.subjects = XYZSubjects([subject], simulation=simulation)
        simulation.subjects.extend(other_subjects)

        proximity_mechanism = MyProximityMechanism(
            config=Config(),
            simulation=simulation,
            subject=subject,
        )

        data = proximity_mechanism.run()
        assert [
            {
                'direction': 0,
                'subject': other_subjects[0],
                'distance': 0.0,
            },
            {
                'direction': 135.0,
                'subject': other_subjects[1],
                'distance': 1.41
            },
            {
                'direction': 135.0,
                'subject': other_subjects[2],
                'distance': 2.83
            },
        ] == data

    def test_str_representation_from_str(self):
        str_ = """
            0 0 1 0 0
            0 1 1 1 0
            0 0 1 0 0
        """
        items_positions = {
            '0': [
                (-2, -1, 0),
                (-1, -1, 0),
                (1, -1, 0),
                (2, -1, 0),
                (-2, 0, 0),
                (2, 0, 0),
                (-2, 1, 0),
                (-1, 1, 0),
                (1, 1, 0),
                (2, 1, 0),
            ],
            '1': [
                (0, -1, 0),
                (-1, 0, 0),
                (0, 0, 0),
                (1, 0, 0),
                (0, 1, 0),
            ],
        }
        assert items_positions == get_positions_from_str_representation(str_)

    def test_str_representation_to_str(self):
        expected = """
            0 0 1 0 0
            0 1 1 1 0
            0 0 1 0 0
        """
        items_positions = {
            '0': [
                (-2, -1, 0),
                (-1, -1, 0),
                (1, -1, 0),
                (2, -1, 0),
                (-2, 0, 0),
                (2, 0, 0),
                (-2, 1, 0),
                (-1, 1, 0),
                (1, 1, 0),
                (2, 1, 0),
            ],
            '1': [
                (0, -1, 0),
                (-1, 0, 0),
                (0, 0, 0),
                (1, 0, 0),
                (0, 1, 0),
            ],
        }

        assert expected == \
            get_str_representation_from_positions(
                items_positions,
                **str_kwargs
            )

    # def test_str_representation_to_str_multi_levels(self):
    #     expected = """
    #         0 0 1 0 0
    #         0 1 1 1 0
    #         0 0 1 0 0
    #         ----
    #         0 0 0 0 0
    #         0 0 1 0 0
    #         0 0 0 0 0
    #     """
    #     items_positions = {
    #         '0': [
    #             (-2, -1, 0),
    #             (-1, -1, 0),
    #             (1, -1, 0),
    #             (2, -1, 0),
    #             (-2, 0, 0),
    #             (2, 0, 0),
    #             (-2, 1, 0),
    #             (-1, 1, 0),
    #             (1, 1, 0),
    #             (2, 1, 0),
    #             (-2, -1, 1),
    #             (-1, -1, 1),
    #             (1, -1, 1),
    #             (2, -1, 1),
    #             (-1, 0, 1),
    #             (-2, 0, 1),
    #             (2, 0, 1),
    #             (-2, 1, 1),
    #             (-1, 1, 1),
    #             (1, 1, 1),
    #             (2, 1, 1),
    #             (2, -1, 1),
    #             (1, 0, 1),
    #             (2, 1, 1),
    #         ],
    #         '1': [
    #             (0, -1, 0),
    #             (-1, 0, 0),
    #             (0, 0, 0),
    #             (1, 0, 0),
    #             (0, 1, 0),
    #             (0, 0, 1),
    #         ],
    #     }
    #
    #     assert expected == \
    #         get_str_representation_from_positions(
    #             items_positions,
    #             **str_kwargs
    #         )
