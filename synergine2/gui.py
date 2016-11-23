import cocos
import pyglet

from synergine2.terminals import Terminal


class Gui(object):
    def __init__(
            self,
            terminal: Terminal,
            read_queue_interval: float= 1/60.0,
    ):
        self._read_queue_interval = read_queue_interval
        self.terminal = terminal
        cocos.director.director.init()

    def run(self):
        pyglet.clock.schedule_interval(
            lambda *_, **__: self.terminal.read(),
            self._read_queue_interval,
        )
        cocos.director.director.run(self.get_main_scene())

    def get_main_scene(self) -> cocos.cocosnode.CocosNode:
        raise NotImplementedError()
