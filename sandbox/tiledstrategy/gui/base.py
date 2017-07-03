# coding: utf-8
import random

from sandbox.tiledstrategy.gui.animation import ANIMATION_WALK
from sandbox.tiledstrategy.gui.animation import ANIMATION_CRAWL
from synergine2_cocos2d.animation import Animate
from synergine2_cocos2d.gui import TMXGui


class Game(TMXGui):
    def before_run(self) -> None:
        # Test
        from sandbox.tiledstrategy.gui.actor import Man
        from cocos import euclid

        for i in range(10):
            x = random.randint(0, 600)
            y = random.randint(0, 300)
            man = Man()
            man.update_position(euclid.Vector2(x, y))
            self.layer_manager.add_subject(man)
            self.layer_manager.set_selectable(man)
            man.scale = 1

            if x % 2:
                man.do(Animate(ANIMATION_WALK, 10, 4))
            else:
                man.do(Animate(ANIMATION_CRAWL, 20, 4))
