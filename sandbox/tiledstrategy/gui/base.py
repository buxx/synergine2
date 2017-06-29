# coding: utf-8
from synergine2_cocos2d.gui import TMXGui


class Game(TMXGui):
    def before_run(self) -> None:
        # Test
        from cocos import euclid
        from synergine2_cocos2d.gui import Actor

        man = Actor('man.png')
        man.update_position(euclid.Vector2(100.0, 100.0))
        self.layer_manager.add_subject(man)
