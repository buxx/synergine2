# coding: utf-8
import typing

from PIL import Image

from synergine2.config import Config
from synergine2_cocos2d.util import PathManager
from synergine2_xyz.exception import UnknownAnimationIndex
from synergine2_xyz.exception import UnknownAnimation

if typing.TYPE_CHECKING:
    from synergine2_cocos2d.actor import Actor


class ImageCache(object):
    def __init__(self) -> None:
        self.cache = {}


class AnimationImageCache(object):
    def __init__(self) -> None:
        self.cache = {}

    def add(
        self,
        animation_name: str,
        image: Image.Image,
    ) -> None:
        self.cache.setdefault(animation_name, []).append(image)

    def get(
        self,
        animation_name: str,
        image_position: int,
    ) -> Image.Image:
        try:
            return self.cache[animation_name][image_position]
        except KeyError:
            raise Exception('TODO')
        except IndexError:
            raise UnknownAnimationIndex(
                'Unknown animation index "{}" for animation "{}"'.format(
                    image_position,
                    animation_name,
                ),
            )

    def get_animation_images(self, animation_name: str) -> typing.List[Image.Image]:
        try:
            return self.cache[animation_name]
        except KeyError:
            raise UnknownAnimation(
                'Unknown animation "{}"'.format(
                    animation_name,
                ),
            )


class ImageCacheManager(object):
    def __init__(
        self,
        actor: 'Actor',
        config: Config,
    ) -> None:
        self.config = config
        self.actor = actor

        self.path_manager = PathManager(config.resolve('global.include_path.graphics'))
        self.animation_cache = AnimationImageCache()

    def build(self) -> None:
        self.build_animation_cache()

    def build_animation_cache(self) -> None:
        cache_dir = self.config.resolve('global.cache_dir_path')
        animation_images = self.actor.animation_image_paths.items()

        for animation_name, animation_image_paths in animation_images:
            for i, animation_image_path in enumerate(animation_image_paths):
                final_image_path = self.path_manager.path(animation_image_path)
                final_image = Image.open(final_image_path)

                for appliable_image in self.actor.get_animation_appliable_images(
                    animation_name,
                    i,
                ):
                    final_image.paste(
                        appliable_image,
                        (0, 0),
                        appliable_image,
                    )

                self.animation_cache.add(animation_name, final_image)
