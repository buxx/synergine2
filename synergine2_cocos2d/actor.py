# coding: utf-8
import io
import os
import typing
import ntpath

import pyglet
from PIL import Image
import cocos
from cocos import collision_model
from cocos import euclid

from synergine2.config import Config
from synergine2.simulation import Subject
from synergine2_cocos2d.animation import AnimatedInterface
from synergine2_cocos2d.util import PathManager
from synergine2_xyz.image import ImageCacheManager


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
        self.build_animation_images(subject.id)
        self.current_image = image
        self.need_update_cshape = False
        self.properties = properties or {}
        self._freeze = False

        self.default_image_path = image_path
        self.image_cache = self.get_image_cache_manager()
        self.image_cache.build()

    def get_image_cache_manager(self) -> ImageCacheManager:
        return ImageCacheManager(self, self.config)

    def build_default_image(self, subject_id: int, base_image_path: str) -> str:
        cache_dir = self.config.resolve('global.cache_dir_path')
        with open(base_image_path, 'rb') as base_image_file:
            base_image = Image.open(base_image_file)

            for default_appliable_image in self.get_default_appliable_images():
                base_image.paste(
                    default_appliable_image,
                    (0, 0),
                    default_appliable_image,
                )

            # FIXME NOW: nom des image utilise au dessus
            final_name = '_'.join([
                str(subject_id),
                ntpath.basename(base_image_path),
            ])
            final_path = os.path.join(cache_dir, final_name)
            base_image.save(final_path)

        return final_path

    def get_default_appliable_images(self) -> typing.List[Image.Image]:
        return []

    def get_animation_appliable_images(
        self,
        animation_name: str,
        animation_position: int,
    ) -> typing.List[Image.Image]:
        return []

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

    def build_animation_images(self, subject_id: int) -> None:
        """
        Fill self.animation_images with self.animation_image_paths
        :return: None
        """
        cache_dir = self.config.resolve('global.cache_dir_path')
        for animation_name, animation_image_paths in self.animation_image_paths.items():
            self.animation_images[animation_name] = []
            for i, animation_image_path in enumerate(animation_image_paths):
                final_image_path = self.path_manager.path(animation_image_path)
                final_image = Image.open(final_image_path)

                for appliable_image in self.get_animation_appliable_images(
                    animation_name,
                    i,
                ):
                    final_image.paste(
                        appliable_image,
                        (0, 0),
                        appliable_image,
                    )

                # FIXME NOW: nom des image utilise au dessus
                final_name = '_'.join([
                    str(subject_id),
                    ntpath.basename(final_image_path),
                ])
                final_path = os.path.join(cache_dir, final_name)

                final_image.save(final_path)

                self.animation_images[animation_name].append(
                    pyglet.image.load(
                        final_path,
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
