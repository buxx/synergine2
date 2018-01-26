# coding: utf-8
import io
import os
import typing
import ntpath

import pyglet

import cocos
from cocos import collision_model
from cocos import euclid

from synergine2.config import Config
from synergine2.simulation import Subject
from synergine2_cocos2d.animation import AnimatedInterface
from synergine2_cocos2d.util import PathManager


class Actor(AnimatedInterface, cocos.sprite.Sprite):
    animation_image_paths = {}  # type: typing.Dict[str, typing.List[str]]

    def __init__(
        self,
        image_path: str,
        subject: Subject,
        position=(0, 0),
        rotation=0,
        scale=1,
        opacity=255,
        color=(255, 255, 255),
        anchor=None,
        properties: dict=None,
        config: Config=None,
        **kwargs
    ):
        # Note: Parameter required, but we want to modify little as possible parent init
        assert config, "Config is a required parameter"
        self.config = config
        self.path_manager = PathManager(config.resolve('global.include_path.graphics'))
        default_image_path = self.build_default_image(
            subject.id,
            self.path_manager.path(image_path),
        )
        image = pyglet.image.load(os.path.abspath(default_image_path))
        self.animation_images = {}  # type: typing.Dict[str, typing.List[pyglet.image.TextureRegion]]  # nopep8
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
        self.properties = properties or {}
        self._freeze = False

    def build_default_image(self, subject_id: int, base_image_path: str) -> str:
        cache_dir = self.config.resolve('global.cache_dir_path', '/tmp')
        with open(base_image_path, 'rb') as base_image_file:

            final_name = '_'.join([
                str(subject_id),
                ntpath.basename(base_image_path),
            ])
            final_path = os.path.join(cache_dir, final_name)
            with open(final_path, 'wb+') as built_image_file:
                built_image_file.write(base_image_file.read())

        return final_path

    def freeze(self) -> None:
        """
        Set object to freeze mode: No visual modification can be done anymore
        """
        self._freeze = True

    def stop_actions(self, action_types: typing.Tuple[typing.Type[cocos.actions.Action], ...]) -> None:
        for action in self.actions:
            if isinstance(action, action_types):
                self.remove_action(action)

    def update_cshape(self) -> None:
        self.cshape = collision_model.AARectShape(
            euclid.Vector2(self.position[0], self.position[1]),
            self.width // 2,
            self.height // 2,
        )
        self.need_update_cshape = False

    def update_position(self, new_position: euclid.Vector2) -> None:
        if self._freeze:
            return

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
                final_image_path = self.path_manager.path(animation_image_path)
                self.animation_images[animation_name].append(
                    pyglet.resource.image(
                        final_image_path,
                    )
                )

    def get_images_for_animation(self, animation_name: str) -> typing.List[pyglet.image.TextureRegion]:
        return self.animation_images.get(animation_name)

    def get_inanimate_image(self) -> pyglet.image.TextureRegion:
        return self.current_image

    def update_image(self, new_image: pyglet.image.TextureRegion):
        if self._freeze:
            return

        self.image = new_image
        self.image_anchor = new_image.width // 2, new_image.height // 2
