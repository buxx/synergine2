# coding: utf-8
import typing

from cocos.audio.pygame.mixer import Sound

from synergine2_cocos2d.util import PathManager


class AudioLibrary(object):
    # name: file_name
    sound_file_paths = {}  # type: typing.Dict[str, str]

    def __init__(
        self,
        include_paths: typing.List[str],
    ) -> None:
        self._path_manager = PathManager(include_paths)
        self._sounds = {}

    def get_sound(self, name: str) -> Sound:
        if name not in self._sounds:
            sound_file_name = self.sound_file_paths[name]
            sound_file_path = self._path_manager.path(sound_file_name)
            self._sounds[name] = Sound(sound_file_path)
        return self._sounds[name]