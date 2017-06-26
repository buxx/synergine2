# coding: utf-8
import cocos
from synergine2_cocos2d.gui import TMXGui


class Game(TMXGui):
    def before_run(self) -> None:
        # Test
        man = cocos.sprite.Sprite('man.png')
        self.layer_manager.subject_layer.add(man)
        man.position = 0, 0
        move = cocos.actions.MoveTo((80, 80), 2)
        man.do(move)
