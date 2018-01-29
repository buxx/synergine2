# coding: utf-8
import os
import typing
from os import path
import shutil
from pathlib import Path

from synergine2_cocos2d.exception import FileNotFound


def get_map_file_path_from_dir(map_dir_path: str) -> str:
    # TODO: path is temp here
    return '{}.tmx'.format(os.path.join(map_dir_path, os.path.basename(map_dir_path)))


class PathManager(object):
    def __init__(
        self,
        include_paths: typing.List[str],
    ) -> None:
        self._include_paths = []  # type: typing.List[str]
        self.include_paths = include_paths

    @property
    def include_paths(self) -> typing.Tuple[str, ...]:
        return tuple(self._include_paths)

    @include_paths.setter
    def include_paths(self, value: typing.List[str]) -> None:
        self._include_paths = value
        self._include_paths.sort(reverse=True)

    def add_included_path(self, included_path: str) -> None:
        self._include_paths.append(included_path)
        self._include_paths.sort(reverse=True)

    def path(self, file_path: str) -> str:
        # Search in configured paths
        for include_path in self._include_paths:
            complete_file_path = path.join(include_path, file_path)
            if path.isfile(complete_file_path):
                return complete_file_path

        # If not in include last chance in current dir
        if path.isfile(file_path):
            return file_path

        raise FileNotFound('File "{}" not found in paths {}'.format(
            file_path,
            self._include_paths,
        ))


def ensure_dir_exist(dir_path, clear_dir: bool=False) -> None:
    """
    Create directories if no exists
    :param dir_path: path of wanted directory to exist
    :param clear_dir: Remove content of given dir
    """
    path_ = Path(dir_path)
    path_.mkdir(parents=False, exist_ok=True)
    if clear_dir:
        shutil.rmtree(dir_path)
        path_.mkdir(parents=False, exist_ok=True)
