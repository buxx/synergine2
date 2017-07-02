# coding: utf-8
import typing

import pyglet
import cocos


class AnimatedInterface(object):
    def get_images_for_animation(self, animation_name: str) -> typing.List[pyglet.image.TextureRegion]:
        raise NotImplementedError()

    def get_inanimate_image(self) -> pyglet.image.TextureRegion:
        """
        Use this function to specify what image have to be used when animation is finished.
        :return: non inanimate pyglet.image.TextureRegion
        """
        raise NotImplementedError()

    def update_image(self, new_image: pyglet.image.TextureRegion):
        raise NotImplementedError()


# TODO: regarder pyglet.image.Animation
class Animate(cocos.actions.IntervalAction):
    def __init__(
        self,
        animation_name: str,
        duration: float,
        cycle_duration: float,
        direction: int=1,
    ):
        super().__init__()
        self.animation_name = animation_name
        self.duration = duration
        self.animation_images = []  # type: typing.List[pyglet.image.TextureRegion]
        self.last_step_elapsed = 0.0  # type: float
        self.step_interval = None  # type: float
        self.cycle_duration = cycle_duration
        self.current_step = 0  # typ: int
        self.target = typing.cast(AnimatedInterface, self.target)
        self.direction = direction

    def __reversed__(self):
        return self.__class__(
            self.animation_name,
            self.duration,
            self.cycle_duration,
            self.direction * -1,
        )

    def start(self):
        super().start()
        self.animation_images = self.target.get_images_for_animation(self.animation_name)
        self.step_interval = self.cycle_duration / len(self.animation_images)

    def stop(self):
        self.target.update_image(self.target.get_inanimate_image())
        super().stop()

    def update(self, t):
        if not self.is_time_for_new_image():
            return

        self.current_step += self.direction
        try:
            new_image = self.animation_images[self.current_step]
        except IndexError:
            self.current_step = 0
            new_image = self.animation_images[0]

        self.target.update_image(new_image)
        self.last_step_elapsed = self._elapsed

    def is_time_for_new_image(self) -> bool:
        return self._elapsed - self.last_step_elapsed >= self.step_interval
