# coding: utf-8
import typing

import pyglet

import cocos
from cocos import collision_model
from cocos import euclid
from synergine2.simulation import Subject
from synergine2_cocos2d.animation import AnimatedInterface


class Actor(AnimatedInterface, cocos.sprite.Sprite):
    animation_image_paths = {}  # type: typing.Dict[str, typing.List[str]]
    animation_images = {}  # type: typing.Dict[str, typing.List[pyglet.image.TextureRegion]]

    def __init__(
        self,
        image: pyglet.image.TextureRegion,
        subject: Subject,
        position=(0, 0),
        rotation=0,
        scale=1,
        opacity=255,
        color=(255, 255, 255),
        anchor=None,
        **kwargs
    ):
        super().__init__(
            image,
            position,
            rotation,
            scale,
            opacity,
            color,
            anchor,
            **kwargs
        )
        self.subject = subject
        self.cshape = None  # type: collision_model.AARectShape
        self.update_cshape()
        self.build_animation_images()
        self.current_image = image
        self.need_update_cshape = False

    def update_cshape(self) -> None:
        self.cshape = collision_model.AARectShape(
            euclid.Vector2(self.position[0], self.position[1]),
            self.width // 2,
            self.height // 2,
        )
        self.need_update_cshape = False

    def update_position(self, new_position: euclid.Vector2) -> None:
        self.position = new_position
        self.cshape.center = new_position  # Note: if remove: strange behaviour: drag change actor position with anomaly

    def build_animation_images(self) -> None:
        """
        Fill self.animation_images with self.animation_image_paths
        :return: None
        """
        for animation_name, animation_image_paths in self.animation_image_paths.items():
            self.animation_images[animation_name] = []
            for animation_image_path in animation_image_paths:
                self.animation_images[animation_name].append(pyglet.resource.image(animation_image_path))

    def get_images_for_animation(self, animation_name: str) -> typing.List[pyglet.image.TextureRegion]:
        return self.animation_images.get(animation_name)

    def get_inanimate_image(self) -> pyglet.image.TextureRegion:
        return self.current_image

    def update_image(self, new_image: pyglet.image.TextureRegion):
        self.image = new_image
        self.image_anchor = new_image.width // 2, new_image.height // 2
