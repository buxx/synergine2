# coding: utf-8
import pytest

from synergine2_xyz.physics import VisibilityMatrix
from tests import BaseTest


class TestVisibilityMatrix(BaseTest):
    def test_initialize_empty_matrix(self):
        visibility = VisibilityMatrix()
        visibility.initialize_empty_matrix('testing', height=0.5, matrix_width=3, matrix_height=2)
        matrix = visibility.get_matrix('testing', height=0.5)

        assert isinstance(matrix, list)

        assert [0.0, 0.0, 0.0] == matrix[0]
        assert [0.0, 0.0, 0.0] == matrix[1]

    def test_update_matrix(self):
        visibility = VisibilityMatrix()
        visibility.initialize_empty_matrix('testing', height=0.5, matrix_width=3, matrix_height=2)
        visibility.update_matrix('testing', height=0.5, x=2, y=1, value=0.5)
        visibility.update_matrix('testing', height=0.5, x=0, y=0, value=0.7)
        matrix = visibility.get_matrix('testing', height=0.5)

        assert [0.7, 0.0, 0.0] == matrix[0]
        assert [0.0, 0.0, 0.5] == matrix[1]

    @pytest.mark.skip(reason='Not implemented yet')
    def test_get_path_positions(self):
        visibility = VisibilityMatrix()
        visibility.initialize_empty_matrix('testing', height=0.5, matrix_width=3, matrix_height=2)
        visibility.update_matrix('testing', height=0.5, x=2, y=1, value=0.5)
        visibility.update_matrix('testing', height=0.5, x=0, y=0, value=0.7)

        path_positions = visibility.get_path_positions(from_=(0, 0), to=(2, 1))
        assert [(0, 0), (0, 1), (1, 2)] == path_positions

    @pytest.mark.skip(reason='Not implemented yet')
    def test_get_path_values(self):
        visibility = VisibilityMatrix()
        visibility.initialize_empty_matrix('testing', height=0.5, matrix_width=3, matrix_height=2)
        visibility.update_matrix('testing', height=0.5, x=2, y=1, value=0.5)
        visibility.update_matrix('testing', height=0.5, x=0, y=0, value=0.7)

        path_positions = visibility.get_path_positions(from_=(0, 0), to=(2, 1))
        path_values = visibility.get_values_for_path(path_positions=path_positions)
        assert [0.7, 0.0, 0.5] == path_values
