# coding: utf-8
from synergine2_xyz.map import TMXMap
from synergine2_xyz.physics import Matrixes
from synergine2_xyz.tmx_utils import fill_matrix
from tests import BaseTest


class TestVisibilityMatrix(BaseTest):
    def test_tmx_to_matrix(self):
        tmx_map = TMXMap('tests/fixtures/map_001.tmx')
        matrixes = Matrixes()

        assert 5 == tmx_map.width
        assert 5 == tmx_map.height

        matrixes.initialize_empty_matrix(
            'visibility',
            matrix_height=5,
            matrix_width=5,
            value_structure=['height', 'opacity'],
        )
        assert [
            [(0.0, 0.0), (0.0, 0.0), (0.0, 0.0), (0.0, 0.0), (0.0, 0.0), ],
            [(0.0, 0.0), (0.0, 0.0), (0.0, 0.0), (0.0, 0.0), (0.0, 0.0), ],
            [(0.0, 0.0), (0.0, 0.0), (0.0, 0.0), (0.0, 0.0), (0.0, 0.0), ],
            [(0.0, 0.0), (0.0, 0.0), (0.0, 0.0), (0.0, 0.0), (0.0, 0.0), ],
            [(0.0, 0.0), (0.0, 0.0), (0.0, 0.0), (0.0, 0.0), (0.0, 0.0), ],
        ] == matrixes.get_matrix('visibility')

        fill_matrix(tmx_map, matrixes, 'terrain', 'visibility', ['height', 'opacity'])
        assert [
            [(0.0, 0.0), (0.0, 0.0),   (0.0, 0.0),   (0.0, 0.0),   (0.0, 0.0), ],
            [(0.0, 0.0), (2.0, 100.0), (2.0, 100.0), (2.0, 100.0), (0.0, 0.0), ],
            [(0.0, 0.0), (2.0, 100.0), (0.0, 0.0),   (2.0, 100.0), (0.0, 0.0), ],
            [(0.0, 0.0), (2.0, 100.0), (2.0, 100.0), (2.0, 100.0), (0.0, 0.0), ],
            [(0.0, 0.0), (0.0, 0.0),   (0.0, 0.0),   (0.0, 0.0),   (0.0, 0.0), ],
        ] == matrixes.get_matrix('visibility')
