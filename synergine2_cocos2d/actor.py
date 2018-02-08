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
from synergine2.log import get_logger
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
        self.animation_images = {}  # type: typing.Dict[str, typing.List[pyglet.image.TextureRegion]]  # nopep8

        default_texture = self._get_default_image_texture()
        super().__init__(
            default_texture,
            position,
            rotation,
            scale,
            opacity,
            color,
            anchor,
            **kwargs
        )

        self.logger = get_logger('Actor', config)

        self.subject = subject
        self.cshape = None  # type: collision_model.AARectShape
        self.update_cshape()
        self.default_texture = default_texture
        self.need_update_cshape = False
        self.properties = properties or {}
        self._freeze = False

        self.animation_textures_cache = {}  # type: typing.Dict[str, typing.List[pyglet.image.TextureRegion]]  # nopep8
        self.mode_texture_cache = {}  # type: typing.Dict[str, pyglet.image.TextureRegion]  # nopep8

        self.default_image_path = image_path
        self.image_cache_manager = self.get_image_cache_manager()
        self.image_cache_manager.build()

        self.build_textures_cache()

    def get_image_cache_manager(self) -> ImageCacheManager:
        return ImageCacheManager(self, self.config)

    def _get_default_image_texture(self) -> pyglet.image.AbstractImage:
        """
        Build and return teh default actor image texture.
        :return: default actor image texture
        """
        cache_dir = self.config.resolve('global.cache_dir_path')
        mode = self.get_default_mode()
        image_path = self.get_mode_image_path(mode)
        final_image_path = self.path_manager.path(image_path)

        image = Image.open(final_image_path)
        image_path = '{}_default_image.png'
        final_image_path = os.path.join(cache_dir, image_path)
        image.save(final_image_path)

        return pyglet.image.load(final_image_path)

    def get_default_mode(self) -> str:
        raise NotImplementedError()

    def get_mode_image_path(self, mode: str) -> str:
        raise NotImplementedError()

    def get_modes(self) -> typing.List[str]:
        raise NotImplementedError()

    def get_mode_appliable_images(self, mode: str) -> typing.List[Image.Image]:
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

    def build_textures_cache(self) -> None:
        self.build_modes_texture_cache()
        self.build_animation_textures_cache()

    def build_modes_texture_cache(self) -> None:
        cache_dir = self.config.resolve('global.cache_dir_path')
        for mode in self.get_modes():
            mode_image_path = self.path_manager.path(self.get_mode_image_path(mode))
            with open(mode_image_path, 'rb') as base_image_file:
                base_image = Image.open(base_image_file)

                for default_appliable_image in self.get_mode_appliable_images(mode):
                    base_image.paste(
                        default_appliable_image,
                        (0, 0),
                        default_appliable_image,
                    )

                final_name = '{}_mode_{}.png'.format(
                    str(self.subject.id),
                    mode,
                )
                final_path = os.path.join(cache_dir, final_name)
                base_image.save(final_path)
                self.mode_texture_cache[mode] = pyglet.image.load(final_path)

    def build_animation_textures_cache(self) -> None:
        cache_dir = self.config.resolve('global.cache_dir_path')
        for animation_name in self.animation_image_paths.keys():
            texture_regions = []
            animation_images = \
                self.image_cache_manager.animation_cache.get_animation_images(
                    animation_name)

            for i, animation_image in enumerate(animation_images):
                cache_image_name = '{}_animation_{}_{}.png'.format(
                    self.subject.id,
                    animation_name,
                    i,
                )
                cache_image_path = os.path.join(cache_dir, cache_image_name)
                animation_image.save(cache_image_path)
                self.animation_textures_cache.setdefault(animation_name, [])\
                    .append(pyglet.image.load(cache_image_path))

    def get_images_for_animation(
        self,
        animation_name: str,
    ) -> typing.List[pyglet.image.TextureRegion]:
        return self.animation_textures_cache[animation_name]

    def get_inanimate_image(self) -> pyglet.image.TextureRegion:
        return self.get_current_mode_texture()

    def get_current_mode_texture(self) -> pyglet.image.TextureRegion:
        try:
            return self.mode_texture_cache[self.mode]
        except KeyError:
            self.logger.debug(
                'No texture for mode "{}" for actor "{}", available: ({})'.format(
                    self.mode,
                    self.__class__.__name__,
                    ', '.join(self.mode_texture_cache.keys()),
                ),
            )
            return self.mode_texture_cache[self.get_default_mode()]

    def reset_default_texture(self) -> None:
        if self._freeze:
            return

        self.image = self.get_current_mode_texture()

    def update_image(self, new_image: pyglet.image.AbstractImage):
        if self._freeze:
            return

        self.image = new_image
        self.image_anchor = new_image.width // 2, new_image.height // 2
