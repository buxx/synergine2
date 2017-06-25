# coding: utf-8
from synergine2.config import Config
from synergine2.log import SynergineLogger


class MapMiddleware(object):
    def __init__(
        self,
        config: Config,
        logger: SynergineLogger,
        map_dir_path: str,
    ) -> None:
        self.config = config
        self.logger = logger
        self.map_dir_path = map_dir_path


class TMXMiddleware(MapMiddleware):
    pass  # TODO

tmx = cocos.tiles.load('maps/003/003.tmx')

background = cocos.sprite.Sprite('background.png')
level0 = tmx['level0']
level1 = tmx['level1']

layer = MainLayer(self.terminal)
layer.add(background, 0)
layer.add(level0, 1)
layer.add(level1, 2)

main_scene = cocos.scene.Scene(layer)

background.set_position(0 + (background.width / 2), 0 + (background.height / 2))
level0.set_view(0, 0, level0.px_width, level0.px_height)
level1.set_view(0, 0, level1.px_width, level1.px_height)

main_scene.position = 0, 0

man = cocos.sprite.Sprite('man.png')
level0.add(man)
man.position = 0, 0
move = cocos.actions.MoveTo((80, 80), 2)
man.do(move)