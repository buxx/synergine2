from synergine2.config import Config
from synergine2_cocos2d.middleware import MapMiddleware

class TestMapMiddleware:
    def test_get_map_file_path(self):
        test = MapMiddleware(Config(), 'map/003')
        assert test.get_map_file_path() == 'map/003/003.tmx'
        test = MapMiddleware(Config(), 'map/003/')
        assert test.get_map_file_path() == 'map/003/003.tmx'

