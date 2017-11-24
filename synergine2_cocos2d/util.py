# coding: utf-8
import os


def get_map_file_path_from_dir(map_dir_path: str) -> str:
    # TODO: path is temp here
    return 'sandbox/tile/{}.tmx'.format(os.path.join(map_dir_path, os.path.basename(map_dir_path)))
