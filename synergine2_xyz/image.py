# coding: utf-8
import typing

from synergine2.config import Config

if typing.TYPE_CHECKING:
    from synergine2_cocos2d.actor import Actor

class ImageCache(object):
    def __init__(self) -> None:
        self.cache = {}


class ImageCacheManager(object):
    def __init__(
        self,
        actor: 'Actor',
        config: Config,
    ) -> None:
        self.config = config
        self.actor = actor

    def build(self) -> None:
        pass
