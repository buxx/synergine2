# coding: utf-8
import cocos
from synergine2_cocos2d.gui import TMXGui


class Game(TMXGui):
    def before_run(self) -> None:
        # Test
        for i in range(0, 100, 20):
            man = cocos.sprite.Sprite('man.png')
            self.layer_manager.subject_layer.add(man)
            # self.layer_manager.subject_layer.cells[0][0].tile = man
            man.position = i+0, i+0
            move = cocos.actions.MoveTo((80, 80), 2)
            man.do(move)
