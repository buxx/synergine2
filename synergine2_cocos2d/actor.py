# coding: utf-8
import typing

import pyglet

import cocos
from cocos import collision_model
from cocos import euclid
from synergine2_cocos2d.animation import AnimatedInterface


class Actor(AnimatedInterface, cocos.sprite.Sprite):
    animation_image_paths = {}  # type: typing.Dict[str, typing.List[str]]
    animation_images = {}  # type: typing.Dict[str, typing.List[pyglet.image.TextureRegion]]

    def __init__(
        self,
        image: pyglet.image.TextureRegion,
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
        self.cshape = collision_model.AARectShape(
            euclid.Vector2(0.0, 0.0),
            self.width,
            self.height,
        )
        self.build_animation_images()
        self.current_image = image

    def update_position(self, new_position: euclid.Vector2) -> None:
        self.position = new_position
        self.cshape.center = new_position

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
