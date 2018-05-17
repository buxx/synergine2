# coding: utf-8
import os
import tempfile
import typing
from xml.etree import ElementTree
from xml.etree.ElementTree import Element

from cocos.tiles import Resource

from synergine2.config import Config
from synergine2.log import get_logger
from synergine2_cocos2d.util import get_map_file_path_from_dir

if typing.TYPE_CHECKING:
    import cocos


class MapLoader(object):
    def load(self, map_file_path: str) -> Resource:
        # import cocos here for prevent test crash when no X server is
        # present
        import cocos

        tree = ElementTree.parse(map_file_path)
        map_element = tree.getroot()

        final_map_content = self.get_sanitized_map_content(map_element, map_file_path)
        new_file = tempfile.NamedTemporaryFile(mode='w+', suffix='.tmx', delete=False)
        new_file.write(final_map_content)
        new_file.seek(0)

        # return the map
        return cocos.tiles.load(new_file.name)

    def get_sanitized_map_content(
        self,
        map_element: Element,
        map_file_path: str,
    ) -> str:
        # Parse tileset to modify path if required
        for tileset_tag in map_element.findall('tileset'):
            if 'source' in tileset_tag.attrib:
                tileset_path = tileset_tag.attrib['source']

                if not os.path.exists(tileset_path):
                    # try with map file relative path
                    map_dir = os.path.dirname(map_file_path)
                    new_path = os.path.join(map_dir, tileset_path)
                    if os.path.exists(new_path):
                        # It is the correct path, update it
                        tileset_new_content = self.get_sanitized_tileset_content(
                            new_path,
                        )

                        new_file = tempfile.NamedTemporaryFile(
                            mode='w+',
                            suffix='.tsx',
                            delete=False,
                        )
                        new_file.write(tileset_new_content)
                        new_file.seek(0)

                        tileset_tag.attrib['source'] = new_file.name

        # Write new file in temporary dir
        map_xml_str = ElementTree.tostring(
            map_element,
            encoding='utf8',
            method='xml',
        )
        return map_xml_str.decode('utf-8')

    def get_sanitized_tileset_content(
        self,
        tileset_path: str,
    ) -> str:
        tileset_dir = os.path.dirname(tileset_path)
        tree = ElementTree.parse(tileset_path)
        tileset_element = tree.getroot()

        image_node = tileset_element.find('image')
        image_path = image_node.attrib['source']

        final_image_path = os.path.join(tileset_dir, image_path)
        image_node.attrib['source'] = final_image_path
        tileset_xml_str = ElementTree.tostring(
            tileset_element,
            encoding='utf8',
            method='xml',
        )
        return tileset_xml_str.decode('utf-8')


class MapMiddleware(object):
    def __init__(
        self,
        config: Config,
        map_dir_path: str,
    ) -> None:
        self.config = config
        self.logger = get_logger(self.__class__.__name__, config)
        self.map_dir_path = map_dir_path
        self.tmx = None

    def get_map_file_path(self) -> str:
        return get_map_file_path_from_dir(self.map_dir_path)

    def init(self) -> None:
        # import cocos here for prevent test crash when no X server is
        # present
        import cocos

        map_file_path = self.get_map_file_path()
        loader = MapLoader()
        self.tmx = loader.load(map_file_path)

    def get_background_sprite(self) -> 'cocos.sprite.Sprite':
        raise NotImplementedError()

    def get_ground_layer(self) -> 'cocos.tiles.RectMapLayer':
        raise NotImplementedError()

    def get_top_layer(self) -> 'cocos.tiles.RectMapLayer':
        raise NotImplementedError()

    def get_world_height(self) -> int:
        raise NotImplementedError()

    def get_world_width(self) -> int:
        raise NotImplementedError()

    def get_cell_height(self) -> int:
        raise NotImplementedError()

    def get_cell_width(self) -> int:
        raise NotImplementedError()


class TMXMiddleware(MapMiddleware):
    def get_background_sprite(self) -> 'cocos.sprite.Sprite':
        # TODO: Extract it from tmx
        import cocos
        return cocos.sprite.Sprite(os.path.join(
            self.map_dir_path,
            'background.png',
        ))

    def get_interior_sprite(self) -> 'cocos.sprite.Sprite':
        # TODO: Extract it from tmx
        import cocos
        return cocos.sprite.Sprite(os.path.join(
            self.map_dir_path,
            'background_interiors.png',
        ))

    def get_ground_layer(self) -> 'cocos.tiles.RectMapLayer':
        assert self.tmx
        return self.tmx['ground']

    def get_top_layer(self) -> 'cocos.tiles.RectMapLayer':
        assert self.tmx
        return self.tmx['top']

    def get_world_height(self) -> int:
        return len(self.tmx['ground'].cells[0])

    def get_world_width(self) -> int:
        return len(self.tmx['ground'].cells)

    def get_cell_height(self) -> int:
        return self.tmx['ground'].cells[0][0].size[1]

    def get_cell_width(self) -> int:
        return self.tmx['ground'].cells[0][0].size[0]
