# coding: utf-8
import pytest

from synergine2_xyz.physics import Matrixes
from tests import BaseTest


class TestVisibilityMatrix(BaseTest):
    def test_initialize_empty_matrix(self):
        visibility = Matrixes()
        visibility.initialize_empty_matrix('testing', matrix_width=3, matrix_height=2, value_structure=['opacity'])
        matrix = visibility.get_matrix('testing')

        assert isinstance(matrix, list)

        assert [(0.0,), (0.0,), (0.0,)] == matrix[0]
        assert [(0.0,), (0.0,), (0.0,)] == matrix[1]

    def test_update_matrix(self):
        visibility = Matrixes()
        visibility.initialize_empty_matrix('testing', matrix_width=3, matrix_height=2, value_structure=['opacity'])
        visibility.update_matrix('testing', x=2, y=1, value=(0.5,))
        visibility.update_matrix('testing', x=0, y=0, value=(0.7,))
        matrix = visibility.get_matrix('testing')

        assert [(0.7,), (0.0,), (0.0,)] == matrix[0]
        assert [(0.0,), (0.0,), (0.5,)] == matrix[1]

    def test_get_path_positions(self):
        visibility = Matrixes()
        visibility.initialize_empty_matrix('testing', matrix_width=3, matrix_height=2, value_structure=['opacity'])
        visibility.update_matrix('testing', x=2, y=1, value=(0.5,))
        visibility.update_matrix('testing', x=0, y=0, value=(0.7,))

        path_positions = visibility.get_path_positions(from_=(0, 0), to=(2, 1))
        assert [(0, 0), (1, 0), (2, 1)] == path_positions

    def test_get_path_values(self):
        visibility = Matrixes()
        visibility.initialize_empty_matrix('testing', matrix_width=3, matrix_height=2, value_structure=['opacity'])
        visibility.update_matrix('testing', x=2, y=1, value=(0.5,))
        visibility.update_matrix('testing', x=0, y=0, value=(0.7,))

        path_positions = visibility.get_path_positions(from_=(0, 0), to=(2, 1))
        path_values = visibility.get_values_for_path('testing', path_positions=path_positions)
        assert [(0.7,), (0.0,), (0.5,)] == path_values

    def test_get_value(self):
        visibility = Matrixes()
        visibility.initialize_empty_matrix('testing', matrix_width=3, matrix_height=2, value_structure=['opacity'])
        visibility.update_matrix('testing', x=2, y=1, value=(0.5,))
        value = visibility.get_value('testing', x=2, y=1, value_name='opacity')
        assert 0.5 == value
