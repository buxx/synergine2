# coding: utf-8
from synergine2_cocos2d.gui import TMXGui
from synergine2_cocos2d.interaction import MoveActorInteraction
from synergine2_cocos2d.interaction import MoveFastActorInteraction
from synergine2_cocos2d.interaction import MoveCrawlActorInteraction


class Game(TMXGui):
    def before_run(self) -> None:
        self.layer_manager.interaction_manager.register(MoveActorInteraction, self.layer_manager)
        self.layer_manager.interaction_manager.register(MoveFastActorInteraction, self.layer_manager)
        self.layer_manager.interaction_manager.register(MoveCrawlActorInteraction, self.layer_manager)

        # Test
        # from sandbox.tile.gui.actor import Man
        # from cocos import euclid
        #
        # for i in range(10):
        #     x = random.randint(0, 600)
        #     y = random.randint(0, 300)
        #     man = Man()
        #     man.update_position(euclid.Vector2(x, y))
        #     self.layer_manager.add_subject(man)
        #     self.layer_manager.set_selectable(man)
        #     man.scale = 1
        #
        #     if x % 2:
        #         man.do(Animate(ANIMATION_WALK, 10, 4))
        #     else:
        #         man.do(Animate(ANIMATION_CRAWL, 20, 4))
